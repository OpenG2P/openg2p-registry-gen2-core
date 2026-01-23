import logging
import importlib
from typing import Optional

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy import select, inspect as sa_inspect
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models import G2PRegisterDefinition, G2PRegisterSection
from ..schemas import RecordData, RegisterTabRecordData
from ..errors import G2PRegistryErrorCodes, G2PRegistryException

_logger = logging.getLogger('g2p-register-hierarchical-service')


class G2PRegisterHierarchicalService(BaseService):
    """
    Service for handling hierarchical register operations.
    Supports traversing master-child relationships between registers.
    """

    async def get_section_records(
        self,
        subject_register_id: str,
        subject_record_id: str,
        section_register_id: str
    ) -> list[RecordData]:
        """
        Get records from section_register that are linked to subject_record.
        Handles both ancestor (traverse down) and descendant (traverse up) relationships.
        If subject_register_id == section_register_id, returns the subject record directly.

        Args:
            subject_register_id: The register we're starting from
            subject_record_id: The specific record (internal_record_id)
            section_register_id: The register we want records from

        Returns:
            List of RecordData from the section register
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate both registers exist
            subject_register: G2PRegisterDefinition = await self._validate_register_definition(
                subject_register_id, session
            )

            # If same register, return the subject record directly
            if subject_register_id == section_register_id:
                return await self._get_same_register_record(
                    subject_register, subject_record_id, session
                )

            section_register: G2PRegisterDefinition = await self._validate_register_definition(
                section_register_id, session
            )

            # Build hierarchy path and determine direction
            path: list[G2PRegisterDefinition] = []
            path, direction = await self._build_register_hierarchy_path(
                subject_register_id, section_register_id, session
            )

            if direction == "DOWN":
                # Subject is ancestor, traverse DOWN to get section records
                return await self._traverse_down_hierarchy(
                    subject_register, subject_record_id, path, session
                )
            elif direction == "UP":
                # Subject is descendant, traverse UP to get section record
                return await self._traverse_up_hierarchy(
                    subject_register, subject_record_id, path, session
                )
            elif direction == "PEER":
                # Subject and section are peers, traverse both directions
                return await self._traverse_peer_hierarchy(
                    subject_register, subject_record_id, path, session
                )

            else:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                    message=f"Register with id {section_register_id} not found"
                )
    
    async def _get_same_register_record(
        self,
        register: G2PRegisterDefinition,
        record_id: str,
        session
    ) -> list[RecordData]:
        """
        Get a record from the same register (no hierarchy traversal needed).

        Args:
            register: The register definition
            record_id: The record's internal_record_id
            session: Database session

        Returns:
            List containing single RecordData
        """
        impl_class = self._get_implementation_class(register.register_mnemonic)
        result = await session.execute(
            select(impl_class).where(
                impl_class.internal_record_id == record_id
            )
        )
        record = result.scalar()

        if not record:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                message=f"Record {record_id} not found in register {register.register_mnemonic}"
            )

        return [self._convert_record_to_record_data(record)]

    async def _validate_register_definition(
        self,
        register_id: str,
        session
    ) -> G2PRegisterDefinition:
        """Validate that a register definition exists."""
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == register_id
                )
            )
        ).scalar()

        if not register_definition:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                message=f"Register with id {register_id} not found"
            )

        return register_definition

    async def _build_register_hierarchy_path(
        self,
        subject_register_id: str,
        section_register_id: str,
        session
    ) -> tuple[list[G2PRegisterDefinition], str]:
        """
        Build the path between two registers and determine direction.

        Returns:
            (path, direction) where direction is "UP" or "DOWN"
            - DOWN: subject is ancestor of section (path goes from section up to subject)
            - UP: subject is descendant of section (path goes from subject up to section)
        """
        # Try finding path going UP from section to subject (subject is ancestor)
        path_from_section: list[G2PRegisterDefinition] | None = await self._find_path_to_ancestor(
            section_register_id, subject_register_id, session
        )
        if path_from_section:
            return (path_from_section, "DOWN")

        # Try finding path going UP from subject to section (subject is descendant)
        path_from_subject: list[G2PRegisterDefinition] | None = await self._find_path_to_ancestor(
            subject_register_id, section_register_id, session
        )
        if path_from_subject:
            return (path_from_subject, "UP")

        # If no path found, try peers
        path_from_peer: list[G2PRegisterDefinition] | None = await self._find_path_to_peer(
            subject_register_id, section_register_id, session
        )
        if path_from_peer:
            return (path_from_peer, "PEER")

        raise G2PRegistryException(
            code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
            message=f"No hierarchy path found between registers {subject_register_id} and {section_register_id}"
        )
    async def _find_path_to_peer(
        self,
        subject_register_id: str,
        section_register_id: str,
        session,
    ) -> list[G2PRegisterDefinition] | None:
        """
        Find path from start_register up to target_register via master_register_id.
        In case of DOWN, start_register is section_register_id, target_register_id is subject_register_id.
        In case of UP, start_register is subject_register_id, target_register_id is section_register_id.
        """
        subject_register: G2PRegisterDefinition | None = await session.get(G2PRegisterDefinition, subject_register_id)
        section_register: G2PRegisterDefinition | None = await session.get(G2PRegisterDefinition, section_register_id)

        if subject_register.master_register_id == section_register.master_register_id:
            return [section_register]

        return None

    async def _find_path_to_ancestor(
        self,
        start_register_id: str,
        target_register_id: str,
        session,
        max_depth: int = 20
    ) -> list[G2PRegisterDefinition] | None:
        """
        Find path from start_register up to target_register via master_register_id.
        In case of DOWN, start_register is section_register_id, target_register_id is subject_register_id.
        In case of UP, start_register is subject_register_id, target_register_id is section_register_id.
        
        Args:
            start_register_id: Starting register
            target_register_id: Target ancestor register
            session: Database session
            max_depth: Maximum hierarchy depth to prevent infinite loops
            
        Returns:
            List of register definitions from start to target, or None if not found
        """
        path: list[G2PRegisterDefinition] = []
        current_id: str | None = start_register_id
        depth: int = 0

        while current_id and depth < max_depth:
            register_definition: G2PRegisterDefinition = (
                await session.execute(
                    select(G2PRegisterDefinition).where(
                        G2PRegisterDefinition.register_id == current_id
                    )
                )
            ).scalar()

            if not register_definition:
                return None

            path.append(register_definition)

            if current_id == target_register_id:
                return path

            current_id = register_definition.master_register_id
            depth += 1

        return None

    def _get_implementation_class(self, register_mnemonic: str):
        """
        Get the implementation class for a register based on its mnemonic.
        
        Args:
            register_mnemonic: The register mnemonic (e.g., "Farmer", "FamilyMember")
            
        Returns:
            The SQLAlchemy model class for the register
        """
        try:
            module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
            register_class_prefix: str = "G2PRegister"
            implementation_class_name: str = f"{register_class_prefix}{register_mnemonic}"
            implementation_class = getattr(module, implementation_class_name)
            return implementation_class
        except (AttributeError, ModuleNotFoundError) as error:
            _logger.error(f"Could not find register class for mnemonic {register_mnemonic}: {str(error)}")
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                message=f"Register implementation not found for {register_mnemonic}"
            )

    def _convert_record_to_record_data(self, record) -> RecordData:
        """
        Convert an ORM record object to RecordData schema.
        Extra fields from the implementation table are flattened at root level.

        Args:
            record: SQLAlchemy ORM record

        Returns:
            RecordData object with flattened extra fields
        """
        from ..helpers import MinioClient

        mapper = sa_inspect(record.__class__)
        extra_fields: dict = {}

        # Get MinIO client for generating presigned URLs
        minio_client: MinioClient = MinioClient.get_component()

        for column in mapper.columns:
            column_name: str = column.name
            value = getattr(record, column_name, None)

            if value is not None and hasattr(value, 'isoformat'):
                value = value.isoformat()

            # Convert image field to record_image_url with presigned URL
            if column_name == 'image' and value:
                extra_fields['record_image_url'] = minio_client.get_url(object_name=value)
            else:
                extra_fields[column_name] = value

        record_data: RecordData = RecordData(
            **extra_fields
        )

        return record_data
    
    async def _traverse_peer_hierarchy(
        self,
        subject_register: G2PRegisterDefinition,
        subject_record_id: str,
        path: list[G2PRegisterDefinition],
        session
    ) -> list[RecordData]:
        
        # Get subject record from subject register
        subject_impl_class = self._get_implementation_class(subject_register.register_mnemonic)
        subject_record = await session.get(subject_impl_class, subject_record_id)
        
        if not subject_record:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                message=f"Subject record {subject_record_id} not found"
            )

        # Get records from section register where section records link_internal_record_id = subject records internal_record_id
        peer_record_impl_class = self._get_implementation_class(path[0].register_mnemonic)
        peer_records = await session.execute(
            select(peer_record_impl_class).where(
                peer_record_impl_class.link_internal_record_id == subject_record.link_internal_record_id
            )
        )
        peer_records = peer_records.scalars().all()

        return [self._convert_record_to_record_data(record) for record in peer_records]


    async def _traverse_down_hierarchy(
        self,
        subject_register: G2PRegisterDefinition,
        subject_record_id: str,
        path: list[G2PRegisterDefinition],
        session
    ) -> list[RecordData]:
        """
        Traverse DOWN from ancestor to descendant, collecting all linked records.

        Args:
            subject_register: The subject register definition (ancestor)
            subject_record_id: The starting record's internal_record_id
            path: Path from related_register (index 0) up to subject_register (last index)
            session: Database session

        Returns:
            List of RecordData from the related_register (path[0])
        """
        # Validate subject record exists
        subject_impl_class = self._get_implementation_class(subject_register.register_mnemonic)
        subject_record = (
            await session.execute(
                select(subject_impl_class).where(
                    subject_impl_class.internal_record_id == subject_record_id
                )
            )
        ).scalar()

        if not subject_record:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                message=f"Subject record {subject_record_id} not found"
            )

        # Reverse path to go from subject (top) to related (bottom)
        path_reversed: list[G2PRegisterDefinition] = list(reversed(path))

        # Start with subject record's internal_record_id
        current_record_ids: list[str] = [subject_record_id]

        # Skip first register (subject), traverse to children
        for i in range(1, len(path_reversed)):
            register_def: G2PRegisterDefinition = path_reversed[i]
            impl_class = self._get_implementation_class(register_def.register_mnemonic)

            # Find all records in this register where link_internal_record_id is in current_record_ids
            result = await session.execute(
                select(impl_class).where(
                    impl_class.link_internal_record_id.in_(current_record_ids)
                )
            )
            records = result.scalars().all()

            if not records:
                return []

            # If this is the last level (related_register), convert to RecordData
            if i == len(path_reversed) - 1:
                return [self._convert_record_to_record_data(r) for r in records]

            # Otherwise, get the internal_record_ids for the next iteration
            current_record_ids = [r.internal_record_id for r in records]

        return []

    async def _traverse_up_hierarchy(
        self,
        subject_register: G2PRegisterDefinition,
        subject_record_id: str,
        path: list[G2PRegisterDefinition],
        session
    ) -> list[RecordData]:
        """
        Traverse UP from descendant to ancestor, following link_internal_record_id.

        Args:
            subject_register: The subject register definition (descendant)
            subject_record_id: The starting record's internal_record_id
            path: Path from subject_register (index 0) up to related_register (last index)
            session: Database session

        Returns:
            List containing single RecordData from the related_register (path[-1])
        """
        current_record_id: str = subject_record_id

        # Start from subject, traverse up using link_internal_record_id
        for i in range(len(path) - 1):
            current_register: G2PRegisterDefinition = path[i]
            impl_class = self._get_implementation_class(current_register.register_mnemonic)

            # Get current record
            result = await session.execute(
                select(impl_class).where(
                    impl_class.internal_record_id == current_record_id
                )
            )
            record = result.scalar()

            if not record:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                    message=f"Record {current_record_id} not found in register {current_register.register_mnemonic}"
                )

            if not record.link_internal_record_id:
                return []

            current_record_id = record.link_internal_record_id

        # Now get the final record from related_register
        related_register: G2PRegisterDefinition = path[-1]
        impl_class = self._get_implementation_class(related_register.register_mnemonic)
        result = await session.execute(
            select(impl_class).where(
                impl_class.internal_record_id == current_record_id
            )
        )
        record = result.scalar()

        if record:
            return [self._convert_record_to_record_data(record)]

        return []

    async def get_tab_records(
        self,
        subject_register_id: str,
        subject_record_id: str,
        tab_id: str
    ) -> list[RegisterTabRecordData]:
        """
        Get all records for a tab, grouped by unique section_register_id.
        Multiple sections with the same section_register_id are deduplicated.

        Args:
            subject_register_id: The register we're starting from
            subject_record_id: The specific record (internal_record_id)
            tab_id: The tab to fetch records for

        Returns:
            List of RegisterTabRecordData, one per unique section_register_id
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate subject register exists
            await self._validate_register_definition(subject_register_id, session)

            # Fetch all sections for this tab
            result = await session.execute(
                select(G2PRegisterSection).where(
                    G2PRegisterSection.register_id == subject_register_id,
                    G2PRegisterSection.tab_id == tab_id
                )
            )
            sections = result.scalars().all()

            if not sections:
                return []

            # Extract unique section_register_ids to avoid duplicate fetches
            unique_section_register_ids: set[tuple[str, bool]] = set()
            for section in sections:
                unique_section_register_ids.add((section.section_register_id, section.is_list))

            # Fetch records for each unique section_register_id
            tab_records: list[RegisterTabRecordData] = []
            for section_register_id in unique_section_register_ids:
                records: list[RecordData] = await self.get_section_records(
                    subject_register_id=subject_register_id,
                    subject_record_id=subject_record_id,
                    section_register_id=section_register_id[0]
                )
                tab_records.append(RegisterTabRecordData(
                    section_register_id=section_register_id[0],
                    is_list=section_register_id[1],
                    records=records
                ))

            return tab_records
