import logging
import uuid
import importlib
from datetime import datetime

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from openg2p_registry_core.schemas.payload import ChangeLogPayload
from sqlalchemy.orm import Session
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models import (
    G2PRegisterChangeLog, G2PRegisterChangeLogPayload, G2PRegisterDefinition,
    G2PRegisterOperation, G2PRegisterVerification, ApprovalStatusEnum,
    DeduplicationRegisterResult, DeduplicationChangelogResult, G2PRegisterSchema,
    G2PRegisterSection
)
from ..schemas import (
    ChangeLogPayload, RegisterSummaryData, ChangeLogSummaryData, RegisterData, ChildRegisterData,
    SearchResultData, ChangeLogSearchResultData, NumberOfVersionsData,
    NumberOfPendingChangeLogsData, ChangeLogData, ChangeLogsData, RecordData,
    VerificationData, VerificationsData, AddVerificationPayload,
    DeduplicationRegisterResultsData, DeduplicationChangelogResultsData,
    DeduplicationRegisterResultData, DeduplicationChangelogResultData,
    RegisterSchemaData, RegisterSectionData, DisplayField
)
from ..errors import G2PRegistryErrorCodes, G2PRegistryException
from .filter_builder import FilterBuilder

_logger = logging.getLogger('g2p-register-service')
_engine = dbengine.get()

class G2PRegisterService(BaseService):

    async def create_change_log(self, change_log_payload: ChangeLogPayload, source_partner_id: str = None):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:

            g2p_register_definition: G2PRegisterDefinition = await self.validate_register_definition(change_log_payload.register_id, session)
            g2p_register_operation: G2PRegisterOperation = await self.validate_operation(change_log_payload.operation_id, session)

            if not g2p_register_operation.is_new_operation:
                # Check whether the record exists with given internal_record_id
                await self.validate_internal_record(g2p_register_definition, change_log_payload.internal_record_id, session)

            g2p_register_change_log: G2PRegisterChangeLog = await self.construct_change_log(change_log_payload, g2p_register_operation, source_partner_id)

            session.add(g2p_register_change_log)
            # Add the payload object if it exists
            if hasattr(g2p_register_change_log, '_payload_to_add'):
                session.add(g2p_register_change_log._payload_to_add)
            await session.commit()
            # Refresh to get any DB defaults
            await session.refresh(g2p_register_change_log)

            return g2p_register_change_log

    async def get_register_summary_data(self) -> list[RegisterSummaryData]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            register_summary_data_list: list[RegisterSummaryData] = await self._fetch_register_summary_data(session)
            return register_summary_data_list

    async def get_changelog_summary_data(self) -> list[ChangeLogSummaryData]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            changelog_summary_data_list: list[ChangeLogSummaryData] = await self._fetch_changelog_summary_data(session)
            return changelog_summary_data_list

    async def get_all_registers(self) -> list[RegisterData]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            all_registers_list: list[RegisterData] = await self._fetch_all_registers(session)
            return all_registers_list

    async def get_child_registers(self, register_id: str) -> list[ChildRegisterData]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self.validate_register_definition(register_id, session)
            child_registers_list: list[ChildRegisterData] = await self._fetch_child_registers(register_id, session)
            return child_registers_list

    async def search_in_a_register(self, register_id: str, search_text: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[SearchResultData], int]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self.validate_register_definition(register_id, session)
            search_results_list, total_items = await self._search_in_register(register_id, search_text, current_page, page_size, sort_by, filter_by, session)
            return search_results_list, total_items

    async def get_change_logs(self, register_id: str, internal_record_id: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[ChangeLogData], int]:
        """Get all change logs for a specific internal record with pagination"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            await self.validate_register_definition(register_id, session)
            change_logs_list, total_items = await self._fetch_change_logs(register_id, internal_record_id, current_page, page_size, sort_by, filter_by, session)
            return change_logs_list, total_items

    async def get_change_log(self, change_log_id: str) -> ChangeLogData:
        """Get a single change log by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            change_log_data: ChangeLogData = await self._fetch_change_log(change_log_id, session)
            return change_log_data

    async def approve_change_log(self, change_log_id: str):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate change log exists and is pending approval
            change_log = await self.validate_change_log_exists(change_log_id, session)
            _logger.info(f"Validated change log for approval: {change_log}")
            await self.validate_change_log_operation(change_log, session)
            # Validate whether verifications are done
            await self.validate_change_log_verifications(change_log, session)
            # Ensure there are no earlier change logs for the internal_record_id pending approval
            await self.validate_change_log_sequence(change_log, session)
            # In case of approval, insert data into register_history 
            await self.insert_into_register_history(change_log, session)
            # Upsert data into register
            await self.insert_into_register(change_log, session)
            # Mark change log as approved
            change_log.approval_status = ApprovalStatusEnum.APPROVED.value
            change_log.approved_by = "system"
            change_log.approved_at = func.now()
            await session.commit()
            await session.refresh(change_log)
            return change_log
    
    async def reject_change_log(self, change_log_id: str, reason: str):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate change log exists and is pending approval
            change_log = await self.validate_change_log_exists(change_log_id, session)
            _logger.info(f"Validated change log for rejection: {change_log}")
            # Mark change log as rejected
            change_log.approval_status = ApprovalStatusEnum.REJECTED.value
            change_log.approved_by = "system" # TODO: Replace with actual user info
            change_log.approved_at = func.now()
            change_log.rejection_reason = reason
            await session.commit()
            await session.refresh(change_log)
            return change_log

    async def validate_change_log_operation(self, g2p_register_change_log: G2PRegisterChangeLog, session) -> None:
        g2p_register_operation: G2PRegisterOperation = (
            await session.execute(
                select(G2PRegisterOperation).where(
                    G2PRegisterOperation.operation_id == g2p_register_change_log.operation_id
                )
            )
        ).scalar()
        if not g2p_register_operation:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.OPERATION_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.OPERATION_NOT_FOUND.value[0]
            )
        # Note: internal_record_id is already set during change log creation in construct_change_log
        # Do not generate a new one here during approval
        


        
    async def validate_change_log_exists(self, change_log_id: str, session) -> G2PRegisterChangeLog:
        _logger.info(f"Validating change log exists for ID: {change_log_id}")
        change_log: G2PRegisterChangeLog = (
            await session.execute(
                select(G2PRegisterChangeLog).where(
                    G2PRegisterChangeLog.change_log_id == change_log_id
                )
            )
        ).scalar()
        if not change_log:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.CHANGE_LOG_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.CHANGE_LOG_NOT_FOUND.value[0]
            )
        if change_log.approval_status != ApprovalStatusEnum.PENDING.value:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.CHANGE_LOG_NOT_IN_PENDING_STATE.value[1],
                message=G2PRegistryErrorCodes.CHANGE_LOG_NOT_IN_PENDING_STATE.value[0]
            )
        return change_log

    async def validate_change_log_verifications(self, change_log: G2PRegisterChangeLog, session) -> None:
        # Count only approved verifications
        approved_verifications_count = (
            await session.execute(
                select(func.count()).select_from(G2PRegisterVerification).where(
                    G2PRegisterVerification.change_log_id == change_log.change_log_id,
                    G2PRegisterVerification.is_approved == True
                )
            )
        ).scalar_one()
        if approved_verifications_count < (change_log.no_of_verifications_required or 0):
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.VERIFICATIONS_PENDING.value[1],
                message=G2PRegistryErrorCodes.VERIFICATIONS_PENDING.value[0]
            )

    async def validate_change_log_sequence(self, change_log: G2PRegisterChangeLog, session) -> None:
        earlier_pending = (
            await session.execute(
                select(G2PRegisterChangeLog).where(
                    G2PRegisterChangeLog.internal_record_id == change_log.internal_record_id,
                    G2PRegisterChangeLog.approval_status == "PENDING",
                    G2PRegisterChangeLog.created_at < change_log.created_at,
                )
            )
        ).scalars().first()
        if earlier_pending:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1],
                message="There are earlier pending change logs for this record"
            )

    async def insert_into_register_history(self, change_log: G2PRegisterChangeLog, session) -> None:
        # Resolve history model class dynamically based on register mnemonic
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == change_log.register_id
                )
            )
        ).scalar()
        if not register_definition:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0]
            )
        module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
        history_class_prefix = "G2PRegisterHistory"
        implementation_class_name = f"{history_class_prefix}{register_definition.register_mnemonic}"
        history_class = getattr(module, implementation_class_name)

        schema_module = importlib.import_module("openg2p_registry_extensions.register_domain.schemas")
        schema_class_prefix = "G2PRegisterHistorySchema"
        schema_class_name = f"{schema_class_prefix}{register_definition.register_mnemonic}"
        history_schema_class = getattr(schema_module, schema_class_name)

        # Fetch the payload from the database
        payload_result = await session.execute(
            select(G2PRegisterChangeLogPayload).where(
                G2PRegisterChangeLogPayload.change_log_id == change_log.change_log_id
            )
        )
        payload = payload_result.scalar()
        change_payload = payload.change_payload if payload else {}

        # Serialize change log payload to history schema
        history_schema_instance = history_schema_class(**(change_payload or {}))

        # Build the history dict excluding None values from schema, then add base fields
        history_dict = {k: v for k, v in history_schema_instance.dict().items() if v is not None}
        history_dict["history_record_id"] = str(uuid.uuid4())
        history_dict["internal_record_id"] = change_log.internal_record_id
        history_dict["change_log_id"] = change_log.change_log_id
        history_dict["created_at"] = datetime.now()
        history_dict["created_by"] = "system"  # TODO: Replace with actual user info
        history_dict["approved_at"] = datetime.now()
        history_dict["approved_by"] = "system"  # TODO: Replace with actual user info
        history_instance = history_class(**history_dict)

        session.add(history_instance)

    async def insert_into_register(self, change_log: G2PRegisterChangeLog, session) -> None:
        # Resolve register model class dynamically based on register mnemonic
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == change_log.register_id
                )
            )
        ).scalar()
        module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
        register_class_prefix = "G2PRegister"
        implementation_class_name = f"{register_class_prefix}{register_definition.register_mnemonic}"
        register_class = getattr(module, implementation_class_name)

        existing = (
            await session.execute(
                select(register_class).where(
                    register_class.internal_record_id == change_log.internal_record_id
                )
            )
        ).scalar()

        schema_module = importlib.import_module("openg2p_registry_extensions.register_domain.schemas")
        schema_class_prefix = "G2PRegisterSchema"
        schema_class_name = f"{schema_class_prefix}{register_definition.register_mnemonic}"
        schema_class = getattr(schema_module, schema_class_name)

        # Fetch the payload from the database
        payload_result = await session.execute(
            select(G2PRegisterChangeLogPayload).where(
                G2PRegisterChangeLogPayload.change_log_id == change_log.change_log_id
            )
        )
        payload = payload_result.scalar()
        change_payload = payload.change_payload if payload else {}

        # Serialize change log payload to register schema for validation
        register_schema_instance = schema_class(**(change_payload or {}))
        if existing:
            for key, value in register_schema_instance.dict().items():
                # Only update values in change log payload
                if key in change_payload:
                    setattr(existing, key, value)
            setattr(existing, "last_approved_at", datetime.now())
            setattr(existing, "last_approved_by", "system")
            new_instance = existing
        else:
            # Build the payload dict excluding None values from schema, then add base fields
            schema_dict = {k: v for k, v in register_schema_instance.dict().items() if v is not None}
            schema_dict["internal_record_id"] = change_log.internal_record_id
            schema_dict["functional_record_id"] = change_log.internal_record_id  # Use internal_record_id as functional_record_id
            schema_dict["created_by"] = "system"  # TODO: Replace with actual user info
            schema_dict["created_at"] = datetime.now()
            schema_dict["last_approved_at"] = datetime.now()
            schema_dict["last_approved_by"] = "system"
            new_instance = register_class(**schema_dict)
            session.add(new_instance)
        

    async def validate_register_definition(self, register_id: str, session) -> G2PRegisterDefinition:
        g2p_register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == register_id
                )
            )
        ).scalar()
        if not g2p_register_definition:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0]
            )
            
        return g2p_register_definition

    async def validate_operation(self, operation_id: str, session) -> G2PRegisterOperation:

        g2p_register_operation: G2PRegisterOperation =(
                await session.execute(
                select(G2PRegisterOperation).where(
                    G2PRegisterOperation.operation_id == operation_id
                )
            )
        ).scalar()
        if not g2p_register_operation:
            raise ValueError(f"Operation with ID {operation_id} does not exist.")
            
        return g2p_register_operation


    async def validate_internal_record(self, g2p_register_definition: G2PRegisterDefinition, internal_record_id: str, session: Session) -> None:

        module = importlib.import_module("openg2p_registry_extensions.register_domain.models")

        register_class_prefix = "G2PRegister"
        implementation_class_name = f"{register_class_prefix}{g2p_register_definition.register_mnemonic}"

        implementation_class = getattr(module, implementation_class_name)
        _logger.debug(f"Validating internal record for class: {implementation_class}")

        internal_record = (
            await session.execute(
                select(implementation_class).where(
                    implementation_class.internal_record_id == internal_record_id
                )
            )
        ).scalar()
        _logger.debug(f"Internal record fetched: {internal_record}")
        if not internal_record:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[0]
            )

    async def construct_change_log(self, change_log_payload: ChangeLogPayload, g2p_register_operation: G2PRegisterOperation, source_partner_id: str = None) -> G2PRegisterChangeLog:
        change_log_id = str(uuid.uuid4())
        if g2p_register_operation.is_new_operation:
            change_log_payload.internal_record_id = str(uuid.uuid4())

        # Create the payload object
        change_log_payload_obj = G2PRegisterChangeLogPayload(
            change_log_id=change_log_id,
            change_payload=change_log_payload.change_payload,
        )

        # Create the change log object
        g2p_register_change_log = G2PRegisterChangeLog(
            change_log_id=change_log_id,
            register_id=change_log_payload.register_id,
            internal_record_id=change_log_payload.internal_record_id,
            operation_id=change_log_payload.operation_id,
            source_partner_id=source_partner_id or "system",
            created_by="system",  # TODO: Replace with actual user info
            created_at=func.now(),
            no_of_verifications_required=g2p_register_operation.no_of_verifications_required,
            no_of_verifications_done=0,
            approval_status=change_log_payload.approval_status.value,
        )

        # Add both objects to session so they're persisted together
        # The payload will be added when the change log is added
        g2p_register_change_log._payload_to_add = change_log_payload_obj
        return g2p_register_change_log

    async def _fetch_register_summary_data(self, session) -> list[RegisterSummaryData]:
        register_definitions: list[G2PRegisterDefinition] = (
            await session.execute(select(G2PRegisterDefinition))
        ).scalars().all()

        register_summary_data_list: list[RegisterSummaryData] = []

        for register_definition in register_definitions:
            total_record_count: int = await self._count_records_for_register(register_definition, session)

            register_summary_data: RegisterSummaryData = RegisterSummaryData(
                register_id=register_definition.register_id,
                register_mnemonic=register_definition.register_mnemonic,
                register_subject=register_definition.register_subject,
                total_record_count=total_record_count
            )
            register_summary_data_list.append(register_summary_data)

        return register_summary_data_list

    async def _fetch_changelog_summary_data(self, session) -> list[ChangeLogSummaryData]:
        register_definitions: list[G2PRegisterDefinition] = (
            await session.execute(select(G2PRegisterDefinition))
        ).scalars().all()

        changelog_summary_data_list: list[ChangeLogSummaryData] = []

        for register_definition in register_definitions:
            total_count: int = await self._count_changelogs_for_register(
                register_definition.register_id, None, session
            )
            approved_count: int = await self._count_changelogs_for_register(
                register_definition.register_id, ApprovalStatusEnum.APPROVED.value, session
            )
            pending_count: int = await self._count_changelogs_for_register(
                register_definition.register_id, ApprovalStatusEnum.PENDING.value, session
            )

            changelog_summary_data: ChangeLogSummaryData = ChangeLogSummaryData(
                register_id=register_definition.register_id,
                register_mnemonic=register_definition.register_mnemonic,
                register_subject=register_definition.register_subject,
                total_count=total_count,
                approved_count=approved_count,
                pending_count=pending_count
            )
            changelog_summary_data_list.append(changelog_summary_data)

        return changelog_summary_data_list

    async def _count_changelogs_for_register(self, register_id: str, approval_status: str | None, session) -> int:
        query = select(func.count()).select_from(G2PRegisterChangeLog).where(
            G2PRegisterChangeLog.register_id == register_id
        )
        if approval_status is not None:
            query = query.where(G2PRegisterChangeLog.approval_status == approval_status)

        count: int = (await session.execute(query)).scalar_one()
        return count

    async def _count_records_for_register(self, register_definition: G2PRegisterDefinition, session) -> int:
        try:
            module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
            register_class_prefix = "G2PRegister"
            implementation_class_name = f"{register_class_prefix}{register_definition.register_mnemonic}"
            register_class = getattr(module, implementation_class_name)

            total_record_count: int = (
                await session.execute(
                    select(func.count()).select_from(register_class)
                )
            ).scalar_one()

            return total_record_count
        except (AttributeError, ModuleNotFoundError) as error:
            _logger.warning(f"Could not find register class for mnemonic {register_definition.register_mnemonic}: {str(error)}")
            return 0

    async def _fetch_all_registers(self, session) -> list[RegisterData]:
        register_definitions: list[G2PRegisterDefinition] = (
            await session.execute(select(G2PRegisterDefinition))
        ).scalars().all()

        all_registers_list: list[RegisterData] = []

        for register_definition in register_definitions:
            register_data: RegisterData = RegisterData(
                register_id=register_definition.register_id,
                register_mnemonic=register_definition.register_mnemonic,
                register_subject=register_definition.register_subject,
                register_description=register_definition.register_description,
                master_register_id=register_definition.master_register_id
            )
            all_registers_list.append(register_data)

        return all_registers_list

    async def _fetch_child_registers(self, parent_register_id: str, session) -> list[ChildRegisterData]:
        child_register_definitions: list[G2PRegisterDefinition] = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.master_register_id == parent_register_id
                )
            )
        ).scalars().all()

        child_registers_list: list[ChildRegisterData] = []

        for register_definition in child_register_definitions:
            child_register_data: ChildRegisterData = ChildRegisterData(
                register_id=register_definition.register_id,
                register_mnemonic=register_definition.register_mnemonic,
                register_subject=register_definition.register_subject,
                register_description=register_definition.register_description
            )
            child_registers_list.append(child_register_data)

        return child_registers_list

    async def _search_in_register(self, register_id: str, search_text: str, current_page: int, page_size: int, sort_by: str, filter_by: dict, session) -> tuple[list[SearchResultData], int]:
        g2p_register_definition: G2PRegisterDefinition = await self.validate_register_definition(register_id, session)

        # Get the implementation class for this register
        try:
            module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
            register_class_prefix: str = "G2PRegister"
            implementation_class_name: str = f"{register_class_prefix}{g2p_register_definition.register_mnemonic}"
            implementation_class = getattr(module, implementation_class_name)
        except (AttributeError, ModuleNotFoundError) as error:
            _logger.error(f"Could not find register class for mnemonic {g2p_register_definition.register_mnemonic}: {str(error)}")
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                message=f"Register implementation not found for {g2p_register_definition.register_mnemonic}"
            )

        # Fetch register schema for display fields and filter configuration
        schema_result = await session.execute(
            select(G2PRegisterSchema).where(G2PRegisterSchema.register_id == register_id)
        )
        register_schema: G2PRegisterSchema = schema_result.scalar()
        search_result_schema: list = register_schema.search_result_schema if register_schema and register_schema.search_result_schema else []
        filter_schema: list = register_schema.filter_schema if register_schema and register_schema.filter_schema else []

        # Sort display fields by order if schema exists
        display_fields_sorted: list = sorted(search_result_schema, key=lambda x: x.get("order", 999)) if search_result_schema else []
        display_field_names: set = {f["field_name"] for f in display_fields_sorted} if display_fields_sorted else set()

        # Search using LIKE with trigram index optimization
        search_query: str = f"%{search_text}%"

        # Build base filter condition (search text)
        filter_conditions: list = [implementation_class.search_text.ilike(search_query)]

        # Build filter conditions using FilterBuilder (with security validations)
        if filter_by:
            filter_builder = FilterBuilder(filter_schema)
            try:
                user_filter_conditions = filter_builder.build_conditions(filter_by, implementation_class)
                filter_conditions.extend(user_filter_conditions)
            except ValueError as validation_error:
                _logger.warning(f"Filter validation error: {validation_error}")
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.INVALID_REQUEST.value[1],
                    message=str(validation_error)
                )

        # Get total count with filters applied
        count_result = await session.execute(
            select(func.count()).select_from(implementation_class).where(*filter_conditions)
        )
        total_items = count_result.scalar_one()

        # Calculate offset
        offset = (current_page - 1) * page_size

        # Build query with filters applied
        query = select(implementation_class).where(*filter_conditions)

        # Apply sorting if provided
        if sort_by:
            try:
                sort_column = getattr(implementation_class, sort_by)
                query = query.order_by(sort_column)
            except AttributeError:
                _logger.warning(f"Sort column {sort_by} not found, using default order")

        # Apply pagination
        query = query.offset(offset).limit(page_size)

        search_results = (
            await session.execute(query)
        ).scalars().all()

        search_results_list: list[SearchResultData] = []

        # Convert ORM objects to SearchResultData while still in session context
        for result in search_results:
            # Build display_fields list from schema with actual values
            display_fields_list: list[DisplayField] = []
            if display_fields_sorted:
                for field_config in display_fields_sorted:
                    field_name: str = field_config.get("field_name")
                    value = getattr(result, field_name, None) if hasattr(result, field_name) else None
                    # Convert datetime objects to string
                    if value is not None and hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    # Convert non-string values to string for consistency
                    if value is not None and not isinstance(value, str):
                        value = str(value)
                    display_fields_list.append(DisplayField(
                        field_name=field_name,
                        value=value,
                        order=field_config.get("order", 999)
                    ))

            # Create SearchResultData object
            search_result_data: SearchResultData = SearchResultData(
                internal_record_id=result.internal_record_id,
                functional_record_id=result.functional_record_id,
                link_record_id=result.link_record_id,
                record_name=result.record_name,
                image=result.image,
                created_by=result.created_by,
                created_at=str(result.created_at.isoformat()) if result.created_at and hasattr(result.created_at, 'isoformat') else None,
                last_approved_at=str(result.last_approved_at.isoformat()) if result.last_approved_at and hasattr(result.last_approved_at, 'isoformat') else None,
                last_approved_by=result.last_approved_by,
                display_fields=display_fields_list if display_fields_list else None
            )
            search_results_list.append(search_result_data)

        return search_results_list, total_items

    async def search_in_change_log(self, search_text: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[ChangeLogSearchResultData], int]:
        """Search in change logs using search_text field with pagination"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            search_results, total_items = await self._search_in_change_log(search_text, current_page, page_size, sort_by, filter_by, session)
            return search_results, total_items

    async def _search_in_change_log(self, search_text: str, current_page: int, page_size: int, sort_by: str, filter_by: dict, session) -> tuple[list[ChangeLogSearchResultData], int]:
        """Helper method to search in change logs with pagination"""
        search_query = f"%{search_text}%"

        # Build base query
        base_query = select(G2PRegisterChangeLog, G2PRegisterChangeLogPayload).join(
            G2PRegisterChangeLogPayload,
            G2PRegisterChangeLog.change_log_id == G2PRegisterChangeLogPayload.change_log_id
        ).where(
            G2PRegisterChangeLogPayload.search_text.ilike(search_query)
        )

        # Get total count
        count_result = await session.execute(select(func.count()).select_from(G2PRegisterChangeLog).join(
            G2PRegisterChangeLogPayload,
            G2PRegisterChangeLog.change_log_id == G2PRegisterChangeLogPayload.change_log_id
        ).where(
            G2PRegisterChangeLogPayload.search_text.ilike(search_query)
        ))
        total_items = count_result.scalar() or 0

        # Apply pagination
        offset = (current_page - 1) * page_size
        query = base_query.offset(offset).limit(page_size)

        result = await session.execute(query)
        search_results = result.all()

        search_results_list: list[ChangeLogSearchResultData] = []

        # Convert ORM objects to ChangeLogSearchResultData while still in session context
        for change_log, payload in search_results:
            # Convert datetime objects to strings
            created_at_str = str(change_log.created_at.isoformat()) if change_log.created_at and hasattr(change_log.created_at, 'isoformat') else None
            approved_at_str = str(change_log.approved_at.isoformat()) if change_log.approved_at and hasattr(change_log.approved_at, 'isoformat') else None

            # Get change_payload from the payload object
            change_payload = payload.change_payload if payload else None

            # Create ChangeLogSearchResultData object
            change_log_search_result: ChangeLogSearchResultData = ChangeLogSearchResultData(
                change_log_id=change_log.change_log_id,
                register_id=change_log.register_id,
                internal_record_id=change_log.internal_record_id,
                operation_id=change_log.operation_id,
                source_partner_id=change_log.source_partner_id,
                created_by=change_log.created_by,
                created_at=created_at_str,
                no_of_verifications_required=change_log.no_of_verifications_required,
                no_of_verifications_done=change_log.no_of_verifications_done,
                approval_status=change_log.approval_status,
                approved_by=change_log.approved_by,
                approved_at=approved_at_str,
                change_payload=change_payload
            )
            search_results_list.append(change_log_search_result)

        return search_results_list, total_items

    async def get_number_of_versions(self, register_id: str, internal_record_id: str) -> NumberOfVersionsData:
        """Get the number of versions (history records) for a given register and internal_record_id"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
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
                    message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0]
                )

            # Dynamically resolve register and history model classes based on register mnemonic
            module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
            register_class_prefix = "G2PRegister"
            history_class_prefix = "G2PRegisterHistory"
            register_class_name = f"{register_class_prefix}{register_definition.register_mnemonic}"
            history_class_name = f"{history_class_prefix}{register_definition.register_mnemonic}"
            register_class = getattr(module, register_class_name)
            history_class = getattr(module, history_class_name)

            # Count history records for the given internal_record_id
            count_result = await session.execute(
                select(func.count()).select_from(history_class).where(
                    history_class.internal_record_id == internal_record_id
                )
            )
            number_of_versions = count_result.scalar_one()

            # Get last_updated_by and last_updated_at from the register record
            register_record = (
                await session.execute(
                    select(register_class).where(
                        register_class.internal_record_id == internal_record_id
                    )
                )
            ).scalar()

            last_updated_by: str = None
            last_updated_at: datetime = None
            if register_record:
                last_updated_by = register_record.last_approved_by
                last_updated_at = register_record.last_approved_at

            # Get last_approved_by and last_approved_at from the latest history record
            latest_history_record = (
                await session.execute(
                    select(history_class).where(
                        history_class.internal_record_id == internal_record_id
                    ).order_by(history_class.approved_at.desc()).limit(1)
                )
            ).scalar()

            last_approved_by: str = None
            last_approved_at: datetime = None
            if latest_history_record:
                last_approved_by = latest_history_record.approved_by
                last_approved_at = latest_history_record.approved_at

            return NumberOfVersionsData(
                register_id=register_id,
                internal_record_id=internal_record_id,
                number_of_versions=number_of_versions,
                last_updated_by=last_updated_by,
                last_updated_at=last_updated_at,
                last_approved_by=last_approved_by,
                last_approved_at=last_approved_at
            )

    async def get_number_of_pending_change_logs(self, register_id: str, internal_record_id: str) -> NumberOfPendingChangeLogsData:
        """Get the number of pending change logs for a given register and internal_record_id"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
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
                    message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0]
                )

            # Count pending change logs for the given internal_record_id
            count_result = await session.execute(
                select(func.count()).select_from(G2PRegisterChangeLog).where(
                    (G2PRegisterChangeLog.register_id == register_id) &
                    (G2PRegisterChangeLog.internal_record_id == internal_record_id) &
                    (G2PRegisterChangeLog.approval_status == ApprovalStatusEnum.PENDING.value)
                )
            )
            number_of_pending_change_logs = count_result.scalar_one()

            return NumberOfPendingChangeLogsData(
                register_id=register_id,
                internal_record_id=internal_record_id,
                number_of_pending_change_logs=number_of_pending_change_logs
            )

    async def _fetch_change_logs(self, register_id: str, internal_record_id: str, current_page: int, page_size: int, sort_by: str, filter_by: dict, session) -> tuple[list[ChangeLogData], int]:
        """Helper method to fetch all change logs for a specific internal record with pagination"""
        # Build base query
        base_query = select(G2PRegisterChangeLog, G2PRegisterChangeLogPayload).join(
            G2PRegisterChangeLogPayload,
            G2PRegisterChangeLog.change_log_id == G2PRegisterChangeLogPayload.change_log_id
        ).where(
            (G2PRegisterChangeLog.register_id == register_id) &
            (G2PRegisterChangeLog.internal_record_id == internal_record_id)
        ).order_by(G2PRegisterChangeLog.created_at.desc())

        # Get total count
        count_result = await session.execute(select(func.count()).select_from(G2PRegisterChangeLog).where(
            (G2PRegisterChangeLog.register_id == register_id) &
            (G2PRegisterChangeLog.internal_record_id == internal_record_id)
        ))
        total_items = count_result.scalar() or 0

        # Apply pagination
        offset = (current_page - 1) * page_size
        query = base_query.offset(offset).limit(page_size)

        result = await session.execute(query)
        change_logs = result.all()

        change_logs_list: list[ChangeLogData] = []

        # Convert ORM objects to ChangeLogData while still in session context
        for change_log, payload in change_logs:
            # Convert datetime objects to strings
            created_at_str = str(change_log.created_at.isoformat()) if change_log.created_at and hasattr(change_log.created_at, 'isoformat') else None
            approved_at_str = str(change_log.approved_at.isoformat()) if change_log.approved_at and hasattr(change_log.approved_at, 'isoformat') else None

            # Get change_payload from the payload object
            change_payload = payload.change_payload if payload else None

            # Create ChangeLogData object
            change_log_data: ChangeLogData = ChangeLogData(
                change_log_id=change_log.change_log_id,
                register_id=change_log.register_id,
                internal_record_id=change_log.internal_record_id,
                operation_id=change_log.operation_id,
                source_partner_id=change_log.source_partner_id,
                created_by=change_log.created_by,
                created_at=created_at_str,
                no_of_verifications_required=change_log.no_of_verifications_required,
                no_of_verifications_done=change_log.no_of_verifications_done,
                approval_status=change_log.approval_status,
                approved_by=change_log.approved_by,
                approved_at=approved_at_str,
                change_payload=change_payload
            )
            change_logs_list.append(change_log_data)

        return change_logs_list, total_items

    async def _fetch_change_log(self, change_log_id: str, session) -> ChangeLogData:
        """Helper method to fetch a single change log by ID"""
        # Join G2PRegisterChangeLog with G2PRegisterChangeLogPayload
        result = await session.execute(
            select(G2PRegisterChangeLog, G2PRegisterChangeLogPayload).join(
                G2PRegisterChangeLogPayload,
                G2PRegisterChangeLog.change_log_id == G2PRegisterChangeLogPayload.change_log_id
            ).where(
                G2PRegisterChangeLog.change_log_id == change_log_id
            )
        )
        change_log_row = result.first()

        if not change_log_row:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.CHANGE_LOG_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.CHANGE_LOG_NOT_FOUND.value[0]
            )

        change_log, payload = change_log_row

        # Convert datetime objects to strings
        created_at_str = str(change_log.created_at.isoformat()) if change_log.created_at and hasattr(change_log.created_at, 'isoformat') else None
        approved_at_str = str(change_log.approved_at.isoformat()) if change_log.approved_at and hasattr(change_log.approved_at, 'isoformat') else None

        # Get change_payload from the payload object
        change_payload = payload.change_payload if payload else None

        # Create ChangeLogData object
        change_log_data: ChangeLogData = ChangeLogData(
            change_log_id=change_log.change_log_id,
            register_id=change_log.register_id,
            internal_record_id=change_log.internal_record_id,
            operation_id=change_log.operation_id,
            source_partner_id=change_log.source_partner_id,
            created_by=change_log.created_by,
            created_at=created_at_str,
            no_of_verifications_required=change_log.no_of_verifications_required,
            no_of_verifications_done=change_log.no_of_verifications_done,
            approval_status=change_log.approval_status,
            approved_by=change_log.approved_by,
            approved_at=approved_at_str,
            change_payload=change_payload
        )

        return change_log_data

    async def get_record(self, register_id: str, internal_record_id: str) -> RecordData:
        """Get a single register record by internal_record_id"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            g2p_register_definition: G2PRegisterDefinition = await self.validate_register_definition(register_id, session)

            # Get the implementation class for this register
            try:
                module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
                register_class_prefix: str = "G2PRegister"
                implementation_class_name: str = f"{register_class_prefix}{g2p_register_definition.register_mnemonic}"
                implementation_class = getattr(module, implementation_class_name)
            except (AttributeError, ModuleNotFoundError) as error:
                _logger.error(f"Could not find register class for mnemonic {g2p_register_definition.register_mnemonic}: {str(error)}")
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[0]
                )

            # Fetch the record by internal_record_id
            record = (
                await session.execute(
                    select(implementation_class).where(
                        implementation_class.internal_record_id == internal_record_id
                    )
                )
            ).scalar()

            if not record:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[0]
                )

            # Convert ORM object to RecordData while still in session context
            mapper = inspect(record.__class__)
            additional_fields: dict = {}

            # Base fields
            base_fields: set = {
                'internal_record_id', 'functional_record_id', 'link_record_id',
                'created_by', 'created_at', 'last_approved_at', 'last_approved_by', 'search_text'
            }

            for column in mapper.columns:
                column_name: str = column.name
                value = getattr(record, column_name, None)

                # Convert datetime objects to strings
                if value is not None and hasattr(value, 'isoformat'):
                    value = value.isoformat()

                # Add to additional_fields if not a base field
                if column_name not in base_fields:
                    additional_fields[column_name] = value

            # Create RecordData object
            record_data: RecordData = RecordData(
                internal_record_id=record.internal_record_id,
                functional_record_id=record.functional_record_id,
                link_record_id=record.link_record_id,
                created_by=record.created_by,
                created_at=str(record.created_at.isoformat()) if record.created_at and hasattr(record.created_at, 'isoformat') else None,
                last_approved_at=str(record.last_approved_at.isoformat()) if record.last_approved_at and hasattr(record.last_approved_at, 'isoformat') else None,
                last_approved_by=record.last_approved_by,
                additional_fields=additional_fields if additional_fields else None
            )

            return record_data

    async def get_verifications_for_change_log(self, change_log_id: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[VerificationData], int]:
        """Get all verifications for a specific change log with pagination"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate change log exists (without checking approval status)
            change_log: G2PRegisterChangeLog = (
                await session.execute(
                    select(G2PRegisterChangeLog).where(
                        G2PRegisterChangeLog.change_log_id == change_log_id
                    )
                )
            ).scalar()
            if not change_log:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.CHANGE_LOG_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.CHANGE_LOG_NOT_FOUND.value[0]
                )

            # Get total count
            count_result = await session.execute(select(func.count()).select_from(G2PRegisterVerification).where(
                G2PRegisterVerification.change_log_id == change_log_id
            ))
            total_items = count_result.scalar() or 0

            # Apply pagination
            offset = (current_page - 1) * page_size
            verifications = (
                await session.execute(
                    select(G2PRegisterVerification).where(
                        G2PRegisterVerification.change_log_id == change_log_id
                    ).order_by(G2PRegisterVerification.verified_at.desc()).offset(offset).limit(page_size)
                )
            ).scalars().all()

            verifications_list: list[VerificationData] = []

            # Convert ORM objects to VerificationData while still in session context
            for verification in verifications:
                verified_at_str = str(verification.verified_at.isoformat()) if verification.verified_at and hasattr(verification.verified_at, 'isoformat') else None

                verification_data: VerificationData = VerificationData(
                    verification_id=verification.verification_id,
                    register_id=verification.register_id,
                    internal_record_id=verification.internal_record_id,
                    operation_id=verification.operation_id,
                    change_log_id=verification.change_log_id,
                    verified_by=verification.verified_by,
                    verified_at=verified_at_str,
                    verification_observations=verification.verification_observations,
                    is_approved=verification.is_approved
                )
                verifications_list.append(verification_data)

            return verifications_list, total_items

    async def add_verification_for_change_log(
        self,
        payload: AddVerificationPayload
    ) -> VerificationData:
        """
        Add a new verification for a change log.

        Args:
            payload: AddVerificationPayload containing change_log_id, verification_observations, is_approved

        Returns:
            VerificationData: The created verification

        Raises:
            G2PRegistryException: If change log not found or other validation errors
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate change log exists
            change_log_result = await session.execute(
                select(G2PRegisterChangeLog).where(
                    G2PRegisterChangeLog.change_log_id == payload.change_log_id
                )
            )
            change_log = change_log_result.scalar_one_or_none()

            if not change_log:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.CHANGE_LOG_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.CHANGE_LOG_NOT_FOUND.value[0]
                )

            # Create new verification
            verification_id = str(uuid.uuid4())
            verification = G2PRegisterVerification(
                verification_id=verification_id,
                register_id=change_log.register_id,
                internal_record_id=change_log.internal_record_id,
                operation_id=change_log.operation_id,
                change_log_id=payload.change_log_id,
                verified_by="system",  # Will be set by controller with actual user
                verified_at=datetime.utcnow(),
                verification_observations=payload.verification_observations,
                is_approved=payload.is_approved
            )

            session.add(verification)
            await session.commit()
            await session.refresh(verification)

            # Return verification data
            verification_data = VerificationData(
                verification_id=verification.verification_id,
                register_id=verification.register_id,
                internal_record_id=verification.internal_record_id,
                operation_id=verification.operation_id,
                change_log_id=verification.change_log_id,
                verified_by=verification.verified_by,
                verified_at=verification.verified_at.isoformat() if verification.verified_at else None,
                verification_observations=verification.verification_observations,
                is_approved=verification.is_approved
            )

            return verification_data

    async def get_deduplication_register_results(self, change_log_id: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[DeduplicationRegisterResultData], int]:
        """
        Get deduplication results for a change log against register records with pagination.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Get total count
            count_result = await session.execute(select(func.count()).select_from(DeduplicationRegisterResult).where(
                DeduplicationRegisterResult.change_log_id == change_log_id
            ))
            total_items = count_result.scalar() or 0

            # Apply pagination
            offset = (current_page - 1) * page_size
            results = (
                await session.execute(
                    select(DeduplicationRegisterResult).where(
                        DeduplicationRegisterResult.change_log_id == change_log_id
                    ).offset(offset).limit(page_size)
                )
            ).scalars().all()

            # Convert to schema objects
            dedup_result_data_list = []
            for result in results:
                dedup_result_data = DeduplicationRegisterResultData(
                    dedup_result_id=result.dedup_result_id,
                    change_log_id=result.change_log_id,
                    internal_record_id=result.internal_record_id,
                    match_score=result.match_score,
                    field_matches=result.field_matches,
                    created_at=result.created_at.isoformat() if result.created_at else None
                )
                dedup_result_data_list.append(dedup_result_data)

            return dedup_result_data_list, total_items

    async def get_deduplication_changelog_results(self, change_log_id: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[DeduplicationChangelogResultData], int]:
        """
        Get deduplication results for a change log against other change logs with pagination.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Get total count
            count_result = await session.execute(select(func.count()).select_from(DeduplicationChangelogResult).where(
                DeduplicationChangelogResult.change_log_id == change_log_id
            ))
            total_items = count_result.scalar() or 0

            # Apply pagination
            offset = (current_page - 1) * page_size
            results = (
                await session.execute(
                    select(DeduplicationChangelogResult).where(
                        DeduplicationChangelogResult.change_log_id == change_log_id
                    ).offset(offset).limit(page_size)
                )
            ).scalars().all()

            # Convert to schema objects
            dedup_result_data_list = []
            for result in results:
                dedup_result_data = DeduplicationChangelogResultData(
                    dedup_result_id=result.dedup_result_id,
                    change_log_id=result.change_log_id,
                    candidate_change_log_id=result.candidate_change_log_id,
                    match_score=result.match_score,
                    field_matches=result.field_matches,
                    created_at=result.created_at.isoformat() if result.created_at else None
                )
                dedup_result_data_list.append(dedup_result_data)

            return dedup_result_data_list, total_items

    async def get_register_schema(self, register_id: str) -> RegisterSchemaData:
        """
        Get register schema configuration for a given register_id.
        Returns deduplication, search result, and filter schema configurations.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            await self.validate_register_definition(register_id, session)

            # Fetch register schema
            register_schema_data: RegisterSchemaData = await self._fetch_register_schema(register_id, session)
            return register_schema_data

    async def get_register_sections(self, register_id: str) -> list[RegisterSectionData]:
        """
        Get register sections for a given register_id.
        Returns a list of section UI schema configurations from g2p_register_sections table.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            await self.validate_register_definition(register_id, session)

            # Fetch register sections
            register_sections_list: list[RegisterSectionData] = await self._fetch_register_sections(register_id, session)
            return register_sections_list

    async def get_register_section(self, register_id: str, section_id: str) -> RegisterSectionData:
        """
        Get a single register section by register_id and section_id.
        Returns the section UI schema configuration from g2p_register_sections table.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            await self.validate_register_definition(register_id, session)

            # Fetch register section
            register_section_data: RegisterSectionData = await self._fetch_register_section(register_id, section_id, session)
            return register_section_data

    async def _fetch_register_schema(self, register_id: str, session) -> RegisterSchemaData:
        """Fetch register schema from database."""
        result = await session.execute(
            select(G2PRegisterSchema).where(G2PRegisterSchema.register_id == register_id)
        )
        register_schema: G2PRegisterSchema = result.scalar()

        if not register_schema:
            # Return empty schema data if no schema exists
            return RegisterSchemaData(
                register_id=register_id,
                deduplicate_schema=None,
                search_result_schema=None,
                filter_schema=None
            )

        return RegisterSchemaData(
            register_id=register_schema.register_id,
            deduplicate_schema=register_schema.deduplicate_schema,
            search_result_schema=register_schema.search_result_schema,
            filter_schema=register_schema.filter_schema
        )

    async def _fetch_register_sections(self, register_id: str, session) -> list[RegisterSectionData]:
        """Fetch register sections from g2p_register_sections table."""
        result = await session.execute(
            select(G2PRegisterSection).where(G2PRegisterSection.register_id == register_id)
        )
        sections = result.scalars().all()

        sections_list: list[RegisterSectionData] = []
        for section in sections:
            section_data = RegisterSectionData(
                register_id=section.register_id,
                section_id=section.section_id,
                section_ui_schema=section.section_ui_schema
            )
            sections_list.append(section_data)

        return sections_list

    async def _fetch_register_section(self, register_id: str, section_id: str, session) -> RegisterSectionData:
        """Fetch a single register section from g2p_register_sections table."""
        result = await session.execute(
            select(G2PRegisterSection).where(
                G2PRegisterSection.register_id == register_id,
                G2PRegisterSection.section_id == section_id
            )
        )
        section: G2PRegisterSection = result.scalar()

        if not section:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.DATA_NOT_FOUND.value[1],
                message=f"Section not found for register_id: {register_id}, section_id: {section_id}"
            )

        return RegisterSectionData(
            register_id=section.register_id,
            section_id=section.section_id,
            section_ui_schema=section.section_ui_schema
        )

    async def create_register(
        self,
        register_mnemonic: str,
        register_description: str | None = None,
        master_register_id: str | None = None,
        dedup_is_enabled: bool = False,
        dedup_threshold_score: float | None = None
    ) -> RegisterData:
        """
        Create a new register definition and a null register schema record.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Check if register_mnemonic already exists
            existing_register = await session.execute(
                select(G2PRegisterDefinition).where(G2PRegisterDefinition.register_mnemonic == register_mnemonic)
            )
            if existing_register.scalar():
                raise ValueError(f"Register with mnemonic '{register_mnemonic}' already exists.")

            # Create the register definition
            register_id: str = str(uuid.uuid4())
            register_definition = G2PRegisterDefinition(
                register_id=register_id,
                register_mnemonic=register_mnemonic,
                register_description=register_description,
                master_register_id=master_register_id,
                dedup_is_enabled=dedup_is_enabled,
                dedup_threshold_score=dedup_threshold_score
            )
            session.add(register_definition)

            # Create a null register schema record
            register_schema = G2PRegisterSchema(
                register_id=register_id,
                deduplicate_schema=None,
                search_result_schema=None,
                filter_schema=None
            )
            session.add(register_schema)

            await session.commit()

            _logger.info(f"Created register definition and schema for mnemonic: {register_mnemonic}")

            return RegisterData(
                register_id=register_id,
                register_mnemonic=register_mnemonic,
                register_subject=register_definition.register_subject,
                register_description=register_description,
                master_register_id=master_register_id
            )

    async def update_register_schema(
        self,
        register_id: str,
        deduplicate_schema: list[dict] | None = None,
        search_result_schema: list[dict] | None = None,
        filter_schema: list[dict] | None = None
    ) -> RegisterSchemaData:
        """
        Update an existing register schema configuration for a given register_id.
        Raises an error if schema does not exist for the register.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            await self.validate_register_definition(register_id, session)

            # Fetch existing schema
            result = await session.execute(
                select(G2PRegisterSchema).where(G2PRegisterSchema.register_id == register_id)
            )
            existing_schema: G2PRegisterSchema = result.scalar()

            if not existing_schema:
                raise ValueError(f"Register schema does not exist for register_id: {register_id}. Use create instead.")

            # Update schema fields only if provided (partial update support)
            if deduplicate_schema is not None:
                existing_schema.deduplicate_schema = deduplicate_schema
            if search_result_schema is not None:
                existing_schema.search_result_schema = search_result_schema
            if filter_schema is not None:
                existing_schema.filter_schema = filter_schema

            await session.commit()

            _logger.info(f"Updated register schema for register_id: {register_id}")

            return RegisterSchemaData(
                register_id=register_id,
                deduplicate_schema=deduplicate_schema,
                search_result_schema=search_result_schema,
                filter_schema=filter_schema
            )
