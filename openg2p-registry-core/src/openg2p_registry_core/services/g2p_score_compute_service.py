import importlib
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import inspect as sqla_inspect
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import async_sessionmaker

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from ..errors import G2PRegistryErrorCodes, G2PRegistryException
from ..models import (
    G2PRegisterChangeRequest,
    G2PRegisterChangeRequestPayload,
    G2PRegisterDefinition,
    G2PRegisterScore,
    G2PRegisterScoreDefinition,
    G2PRegisterScoreHistory,
    G2PScoreComputeQueue,
    RegisterPurposeEnum,
)
from ..schemas import ScoreDefinitionData, ScoreData, ScoreHistoryData
from ..models.g2p_score_compute_queue import ProcessStatusEnum as ScoreProcessStatusEnum

_logger = logging.getLogger('g2p-score-compute-service')


class G2PScoreComputeService(BaseService):
    """
    Core infrastructure for score computation:
    - manages score-definition CRUD
    - populates `G2PScoreComputeQueue` on Change Request approval
    """

    # ----------------------------
    # Score compute queue trigger
    # ----------------------------
    async def enqueue_score_computations(
        self,
        change_request: G2PRegisterChangeRequest,
        session: Session,
    ) -> None:
        """
        Populate/refresh PENDING rows in `g2p_score_compute_queue` for every
        score type whose contributing attributes intersect with the approved CR payload.
        
        Args:
            change_request: The approved change request that triggered score computation
            session: Database session for database operations
            
        Returns:
            None
        """
        
        _logger.info(f"enqueue_score_computations called for change_request_id: {change_request.change_request_id}, section_register_id: {change_request.section_register_id}")

        register_definition = await session.get(
            G2PRegisterDefinition, change_request.section_register_id
        )
        if not register_definition:
            return

        # Guard: only registers with purpose = REGISTER
        if register_definition.register_purpose != RegisterPurposeEnum.REGISTER.value:
            return

        score_definitions = (
            await session.execute(
                select(G2PRegisterScoreDefinition).where(
                    G2PRegisterScoreDefinition.register_id == register_definition.register_id,
                    G2PRegisterScoreDefinition.is_enabled.is_(True),
                )
            )
        ).scalars().all()
        if not score_definitions:
            return

        payload = (
            await session.execute(
                select(G2PRegisterChangeRequestPayload).where(
                    G2PRegisterChangeRequestPayload.change_request_id
                    == change_request.change_request_id
                )
            )
        ).scalar()
        if not payload or payload.change_payload is None:
            return

        payload_items = payload.change_payload
        if isinstance(payload_items, dict):
            payload_items = [payload_items]
        elif not isinstance(payload_items, list):
            payload_items = []

        touched_payload_keys: set[str] = set()
        for item in payload_items:
            if not isinstance(item, dict):
                continue
            touched_payload_keys |= set(self._flatten_dict_keys(item).keys())

        if not touched_payload_keys:
            return

        # Load the current domain register record once (snapshot values for all scores)
        domain_register_class = self._load_register_model(
            register_mnemonic=register_definition.register_mnemonic
        )
        if domain_register_class is None:
            return

        domain_record = (
            await session.execute(
                select(domain_register_class).where(
                    domain_register_class.internal_record_id
                    == change_request.internal_record_id
                )
            )
        ).scalar()
        if not domain_record:
            return

        record_root = self._build_record_root(domain_record)

        # For each score definition, compute the snapshot of *all* contributing values
        # from the current domain record (not just the changed keys).
        for score_definition in score_definitions:
            contributing_paths = score_definition.contributing_attributes or []
            if not isinstance(contributing_paths, list) or not contributing_paths:
                continue

            if not any(path in touched_payload_keys for path in contributing_paths):
                continue

            contributing_values: dict[str, Any] = {
                path: self._get_value_by_dot_path(record_root, path)
                for path in contributing_paths
            }

            await self._upsert_pending_queue_row(
                session=session,
                register_id=register_definition.register_id,
                internal_record_id=change_request.internal_record_id,
                change_request_id=change_request.change_request_id,
                score_definition_id=score_definition.score_definition_id,
                score_type=score_definition.score_type,
                contributing_attribute_values=contributing_values,
            )

    # ----------------------------
    # Queue upsert helpers
    # ----------------------------
    async def _upsert_pending_queue_row(
        self,
        session: Session,
        register_id: str,
        internal_record_id: str,
        change_request_id: str,
        score_definition_id: str,
        score_type: str,
        contributing_attribute_values: dict[str, Any],
    ) -> None:
        """
        Upsert a PENDING row in the score compute queue.
        
        Args:
            session: Database session
            register_id: Register ID
            internal_record_id: Internal record ID
            change_request_id: Change request ID
            score_definition_id: Score definition ID
            score_type: Score type
            contributing_attribute_values: Contributing attribute values
        """
        existing_pending_queue_item: Optional[G2PScoreComputeQueue] = (
            await session.execute(
                select(G2PScoreComputeQueue).where(
                    G2PScoreComputeQueue.internal_record_id == internal_record_id,
                    G2PScoreComputeQueue.score_type == score_type,
                    G2PScoreComputeQueue.compute_status == ScoreProcessStatusEnum.PENDING.value,
                )
            )
        ).scalar()

        if existing_pending_queue_item:
            existing_pending_queue_item.change_request_id = change_request_id
            existing_pending_queue_item.contributing_attribute_values = contributing_attribute_values
            existing_pending_queue_item.compute_no_of_attempts = 0
            existing_pending_queue_item.compute_latest_timestamp = None
            existing_pending_queue_item.compute_latest_error_code = None
            existing_pending_queue_item.compute_status = ScoreProcessStatusEnum.PENDING.value
            session.add(existing_pending_queue_item)
            return

        new_queue_item: G2PScoreComputeQueue = G2PScoreComputeQueue(
            register_id=register_id,
            internal_record_id=internal_record_id,
            score_definition_id=score_definition_id,
            score_type=score_type,
            change_request_id=change_request_id,
            contributing_attribute_values=contributing_attribute_values,
            compute_status=ScoreProcessStatusEnum.PENDING.value,
        )
        session.add(new_queue_item)

    # ----------------------------
    # Score result fetch (used by controller later)
    # ----------------------------
    async def get_scores_for_record(self, internal_record_id: str, session: Session) -> list[ScoreData]:
        """
        Get all scores for a specific record.
        
        Args:
            internal_record_id: Internal record ID
            session: Database session
            
        Returns:
            List of score data objects for the record
        """
        score_records: List[G2PRegisterScore] = (
            await session.execute(
                select(G2PRegisterScore).where(
                    G2PRegisterScore.internal_record_id == internal_record_id
                )
            )
        ).scalars().all()
        
        scores_data: List[ScoreData] = [
            ScoreData(
                score_type=score.score_type,
                computed_score=score.computed_score,
                computed_at=str(score.computed_at) if score.computed_at else None,
                triggered_by_cr_id=score.triggered_by_cr_id,
            )
            for score in score_records
        ]
        return scores_data

    async def get_score_history(
        self, internal_record_id: str, score_type: str, session: Session
    ) -> list[ScoreHistoryData]:
        """
        Get score history for a specific record and score type.
        
        Args:
            internal_record_id: Internal record ID
            score_type: Score type
            session: Database session
            
        Returns:
            List of score history data objects
        """
        score_history_records: List[G2PRegisterScoreHistory] = (
            await session.execute(
                select(G2PRegisterScoreHistory).where(
                    G2PRegisterScoreHistory.internal_record_id == internal_record_id,
                    G2PRegisterScoreHistory.score_type == score_type,
                )
            )
        ).scalars().all()
        
        score_history_data: List[ScoreHistoryData] = [
            ScoreHistoryData(
                computed_score=score.computed_score,
                computed_at=str(score.computed_at) if score.computed_at else None,
                triggered_by_cr_id=score.triggered_by_cr_id,
            )
            for score in score_history_records
        ]
        return score_history_data

    # ----------------------------
    # Definition CRUD (minimal; enough to seed)
    # ----------------------------
    async def get_score_definitions_for_register(
        self, register_id: str, session: Session
    ) -> list[ScoreDefinitionData]:
        """
        Get all score definitions for a register.
        
        Args:
            register_id: Register ID
            session: Database session
            
        Returns:
            List of score definition data objects
        """
        score_definition_records: List[G2PRegisterScoreDefinition] = (
            await session.execute(
                select(G2PRegisterScoreDefinition).where(
                    G2PRegisterScoreDefinition.register_id == register_id
                )
            )
        ).scalars().all()
        
        score_definitions_data: List[ScoreDefinitionData] = [
            ScoreDefinitionData(
                score_definition_id=score_definition.score_definition_id,
                score_type=score_definition.score_type,
                contributing_attributes=score_definition.contributing_attributes or [],
                score_config=score_definition.score_config,
                is_enabled=score_definition.is_enabled,
            )
            for score_definition in score_definition_records
        ]
        return score_definitions_data

    async def create_score_definition(
        self,
        *,
        register_id: str,
        score_type: str,
        contributing_attributes: list[str],
        score_config: dict[str, Any] | None,
        session: Session,
    ) -> ScoreDefinitionData:
        """
        Create a new score definition.
        
        Args:
            register_id: Register ID
            score_type: Score type
            contributing_attributes: List of contributing attribute paths
            score_config: Score configuration parameters
            session: Database session
            
        Returns:
            Created score definition data object
        """
        # Guard: only registers with purpose = REGISTER
        register_definition = await session.get(G2PRegisterDefinition, register_id)
        if not register_definition or register_definition.register_purpose != RegisterPurposeEnum.REGISTER.value:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.SCORE_DEFINITION_NOT_ALLOWED_FOR_REGISTER_PURPOSE.value[1],
                message="Score definitions are only allowed for registers with register_purpose = REGISTER",
            )

        if not isinstance(contributing_attributes, list) or not contributing_attributes:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.SCORE_DEFINITION_CONTRIBUTING_ATTRIBUTES_INVALID.value[1],
                message="contributing_attributes must be a non-empty list of dot-path strings",
            )

        existing_score_definition: Optional[G2PRegisterScoreDefinition] = (
            await session.execute(
                select(G2PRegisterScoreDefinition).where(
                    G2PRegisterScoreDefinition.register_id == register_id,
                    G2PRegisterScoreDefinition.score_type == score_type,
                )
            )
        ).scalar()

        if existing_score_definition:
            existing_score_definition.contributing_attributes = contributing_attributes
            existing_score_definition.score_config = score_config or {}
            existing_score_definition.is_enabled = True
            session.add(existing_score_definition)
            await session.flush()
            created_score_definition: G2PRegisterScoreDefinition = existing_score_definition
        else:
            new_score_definition: G2PRegisterScoreDefinition = G2PRegisterScoreDefinition(
                register_id=register_id,
                score_type=score_type,
                contributing_attributes=contributing_attributes,
                score_config=score_config or {},
                is_enabled=True,
            )
            session.add(new_score_definition)
            await session.flush()
            created_score_definition = new_score_definition
        
        return ScoreDefinitionData(
            score_definition_id=created_score_definition.score_definition_id,
            score_type=created_score_definition.score_type,
            contributing_attributes=created_score_definition.contributing_attributes or [],
            score_config=created_score_definition.score_config,
            is_enabled=created_score_definition.is_enabled,
        )

    async def update_score_definition(
        self,
        *,
        score_definition_id: str,
        contributing_attributes: list[str] | None,
        score_config: dict[str, Any] | None,
        is_enabled: bool | None,
        session: Session,
    ) -> ScoreDefinitionData:
        """
        Update an existing score definition.
        
        Args:
            score_definition_id: Score definition ID
            contributing_attributes: List of contributing attribute paths
            score_config: Score configuration parameters
            is_enabled: Whether the score definition is enabled
            session: Database session
            
        Returns:
            Updated score definition data object
        """
        score_definition_to_update: Optional[G2PRegisterScoreDefinition] = await session.get(
            G2PRegisterScoreDefinition, score_definition_id
        )
        if not score_definition_to_update:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.SCORE_DEFINITION_NOT_FOUND.value[1],
                message=f"Score definition not found: {score_definition_id}",
            )

        register_definition: Optional[G2PRegisterDefinition] = await session.get(
            G2PRegisterDefinition, score_definition_to_update.register_id
        )
        # Enforce guard at service layer.
        if (
            not register_definition
            or register_definition.register_purpose != RegisterPurposeEnum.REGISTER.value
        ):
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.SCORE_DEFINITION_NOT_ALLOWED_FOR_REGISTER_PURPOSE.value[1],
                message="Score definitions are only allowed for registers with register_purpose = REGISTER",
            )

        if contributing_attributes is not None:
            if not isinstance(contributing_attributes, list) or not contributing_attributes:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.SCORE_DEFINITION_CONTRIBUTING_ATTRIBUTES_INVALID.value[1],
                    message="contributing_attributes must be a non-empty list of dot-path strings",
                )
            score_definition_to_update.contributing_attributes = contributing_attributes

        if score_config is not None:
            score_definition_to_update.score_config = score_config

        if is_enabled is not None:
            score_definition_to_update.is_enabled = is_enabled

        session.add(score_definition_to_update)
        await session.flush()
        
        return ScoreDefinitionData(
            score_definition_id=score_definition_to_update.score_definition_id,
            score_type=score_definition_to_update.score_type,
            contributing_attributes=score_definition_to_update.contributing_attributes or [],
            score_config=score_definition_to_update.score_config,
            is_enabled=score_definition_to_update.is_enabled,
        )

    # ----------------------------
    # Dict/path helpers
    # ----------------------------
    def _flatten_dict_keys(self, data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        """
        Flattens nested dicts into dot-paths.
        Example: {"household": {"member_count": 4}} -> {"household.member_count": 4}
        """
        if not isinstance(data, dict):
            return {}

        out: dict[str, Any] = {}
        for k, v in data.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                # Include the prefix key as touched as well, so score definitions
                # that reference a parent path (e.g. "household") still match.
                out[key] = v
                out.update(self._flatten_dict_keys(v, prefix=key))
            else:
                out[key] = v
        return out

    def _build_record_root(self, record) -> dict[str, Any]:
        """
        Convert a SQLAlchemy register model instance into a dict keyed by
        column names. JSON columns remain as dicts to support dot-path traversal.
        
        Args:
            record: The SQLAlchemy model instance
            
        Returns:
            Dictionary representation of the record
        """
        mapper = sqla_inspect(record).mapper
        return {col.key: getattr(record, col.key) for col in mapper.columns}

    def _get_value_by_dot_path(self, root: dict[str, Any], path: str) -> Any:
        """
        Traverse dot-separated paths inside nested dicts.
        
        Args:
            root: The root dictionary to traverse
            path: Dot-separated path to traverse
            
        Returns:
            The value at the specified path or None if not found
        """
        parts = path.split(".") if path else []
        current: Any = root
        for part in parts:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            else:
                # Allow traversal across non-dict objects that store attributes
                current = getattr(current, part, None)
        return current

    def _load_register_model(self, *, register_mnemonic: str):
        """
        Load domain register model class from extensions using the same naming
        convention as the core register write-path.
        
        Args:
            register_mnemonic: The register mnemonic to load the model for
            
        Returns:
            The register model class or None if not found
        """
        try:
            module = importlib.import_module(
                "openg2p_registry_extensions.register_domain.models"
            )
            class_name = f"G2PRegister{register_mnemonic}"
            return getattr(module, class_name)
        except Exception as exc:
            _logger.error("Unable to load register model %s: %s", register_mnemonic, exc)
            return None

