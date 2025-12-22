import logging
import uuid
import importlib
import inspect
from datetime import datetime

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from openg2p_registry_core.schemas.payload import ChangeLogRequestPayload
from sqlalchemy.orm import Session
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models import (
    G2PRegisterChangeLog, G2PRegisterChangeLogPayload, G2PRegisterDefinition,
    G2PRegisterSection, G2PRegisterVerification, ApprovalStatusEnum,
    DeduplicationRegisterResult, DeduplicationChangelogResult, G2PRegisterSchema,
    G2PRegisterSection, G2PRegisterUITab
)
from ..schemas import (
    ChangeLogRequestPayload, RegisterSummaryData, ChangeLogSummaryData, RegisterData, ChildRegisterData,
    RegisterUITabData, SearchResultData, ChangeLogSearchResultData, NumberOfVersionsData,
    NumberOfPendingChangeLogsData, NumberOfCrossRegisterChangesData,
    CrossRegisterChangeLogData, CrossRegisterChangesData,
    ChangeLogData, ChangeLogsData, RecordData,
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

    async def create_change_log(self, change_log_request_payload: ChangeLogRequestPayload, source_partner_id: str = None):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:

            g2p_register_definition: G2PRegisterDefinition = await self.validate_register_definition(change_log_request_payload.register_id, session)
            g2p_register_section: G2PRegisterSection = await self.validate_section(change_log_request_payload.section_id, session)

            # Extract internal_record_id from change_payload if present
            # Note: For new record creation, internal_record_id may be a new UUID that doesn't exist yet
            # We don't validate internal_record_id existence here - it will be created when the change log is approved

            g2p_register_change_log: G2PRegisterChangeLog = await self.construct_change_log(change_log_request_payload, g2p_register_section, source_partner_id)

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

    async def get_changelog_summary_data(self) -> ChangeLogSummaryData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            changelog_summary_data: ChangeLogSummaryData = await self._fetch_changelog_summary_data(session)
            return changelog_summary_data

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

    async def get_master_register(self, register_id: str) -> RegisterData | None:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            register_definition: G2PRegisterDefinition = await self.validate_register_definition(register_id, session)
            master_register_data: RegisterData | None = await self._fetch_master_register(register_definition, session)
            return master_register_data

    async def get_register_tabs(self, register_id: str) -> list[RegisterUITabData]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self.validate_register_definition(register_id, session)
            register_tabs_list: list[RegisterUITabData] = await self._fetch_register_tabs(register_id, session)
            return register_tabs_list

    async def add_register_tab(self, register_id: str, tab_label: str, tab_order: int = 0) -> RegisterUITabData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self.validate_register_definition(register_id, session)
            register_tab_data: RegisterUITabData = await self._create_register_tab(register_id, tab_label, tab_order, session)
            return register_tab_data

    async def _create_register_tab(self, register_id: str, tab_label: str, tab_order: int, session) -> RegisterUITabData:
        new_tab: G2PRegisterUITab = G2PRegisterUITab(
            register_id=register_id,
            tab_label=tab_label,
            tab_order=tab_order
        )
        session.add(new_tab)
        await session.commit()
        await session.refresh(new_tab)

        tab_data: RegisterUITabData = RegisterUITabData(
            tab_id=new_tab.tab_id,
            register_id=new_tab.register_id,
            tab_label=new_tab.tab_label,
            tab_order=new_tab.tab_order
        )
        return tab_data

    async def delete_register_tab(self, tab_id: str) -> RegisterUITabData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            register_tab_data: RegisterUITabData = await self._delete_register_tab(tab_id, session)
            return register_tab_data

    async def _delete_register_tab(self, tab_id: str, session) -> RegisterUITabData:
        tab: G2PRegisterUITab | None = await session.get(G2PRegisterUITab, tab_id)
        if not tab:
            raise ValueError(f"Tab with tab_id '{tab_id}' not found.")

        tab_data: RegisterUITabData = RegisterUITabData(
            tab_id=tab.tab_id,
            register_id=tab.register_id,
            tab_label=tab.tab_label,
            tab_order=tab.tab_order
        )

        await session.delete(tab)
        await session.commit()

        return tab_data

    async def add_register_section(
        self,
        section_register_id: str,
        register_id: str,
        tab_id: str,
        section_mnemonic: str,
        section_description: str = None,
        documents_required: bool = False,
        no_of_verifications_required: int = 0,
        auto_approval: bool = False,
        is_list: bool = False,
        section_ui_schema: dict = None
    ) -> RegisterSectionData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self.validate_register_definition(register_id, session)
            await self._validate_register_tab(register_id, tab_id, session)
            section_data: RegisterSectionData = await self._create_register_section(
                section_register_id, register_id, tab_id, section_mnemonic, section_description,
                documents_required, no_of_verifications_required, auto_approval,
                is_list, section_ui_schema, session
            )
            return section_data

    async def _validate_register_tab(self, register_id: str, tab_id: str, session) -> G2PRegisterUITab:
        tab: G2PRegisterUITab | None = await session.get(G2PRegisterUITab, tab_id)
        if not tab:
            raise ValueError(f"Tab with tab_id '{tab_id}' not found.")
        if tab.register_id != register_id:
            raise ValueError(f"Tab '{tab_id}' does not belong to register '{register_id}'.")
        return tab

    async def _create_register_section(
        self,
        section_register_id: str,
        register_id: str,
        tab_id: str,
        section_mnemonic: str,
        section_description: str,
        documents_required: bool,
        no_of_verifications_required: int,
        auto_approval: bool,
        is_list: bool,
        section_ui_schema: dict,
        session
    ) -> RegisterSectionData:
        new_section: G2PRegisterSection = G2PRegisterSection(
            section_register_id=section_register_id,
            register_id=register_id,
            tab_id=tab_id,
            section_mnemonic=section_mnemonic,
            section_description=section_description,
            documents_required=documents_required,
            no_of_verifications_required=no_of_verifications_required,
            auto_approval=auto_approval,
            is_list=is_list,
            section_ui_schema=section_ui_schema
        )
        session.add(new_section)
        await session.commit()
        await session.refresh(new_section)

        section_data: RegisterSectionData = RegisterSectionData(
            section_register_id=new_section.section_register_id,
            register_id=new_section.register_id,
            section_id=new_section.section_id,
            tab_id=new_section.tab_id,
            section_mnemonic=new_section.section_mnemonic,
            section_description=new_section.section_description,
            documents_required=new_section.documents_required,
            no_of_verifications_required=new_section.no_of_verifications_required,
            auto_approval=new_section.auto_approval,
            is_list=new_section.is_list,
            section_ui_schema=new_section.section_ui_schema
        )
        return section_data

    async def delete_register_section(self, register_id: str, section_id: str) -> RegisterSectionData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            section_data: RegisterSectionData = await self._delete_register_section(register_id, section_id, session)
            return section_data

    async def _delete_register_section(self, register_id: str, section_id: str, session) -> RegisterSectionData:
        section: G2PRegisterSection | None = await session.get(G2PRegisterSection, (register_id, section_id))
        if not section:
            raise ValueError(f"Section with register_id '{register_id}' and section_id '{section_id}' not found.")

        section_data: RegisterSectionData = RegisterSectionData(
            register_id=section.register_id,
            section_id=section.section_id,
            tab_id=section.tab_id,
            section_mnemonic=section.section_mnemonic,
            section_description=section.section_description,
            documents_required=section.documents_required,
            no_of_verifications_required=section.no_of_verifications_required,
            auto_approval=section.auto_approval,
            is_list=section.is_list,
            section_ui_schema=section.section_ui_schema
        )

        await session.delete(section)
        await session.commit()

        return section_data

    async def update_register_section(
        self,
        register_id: str,
        section_id: str,
        tab_id: str = None,
        section_mnemonic: str = None,
        section_description: str = None,
        documents_required: bool = None,
        no_of_verifications_required: int = None,
        auto_approval: bool = None,
        is_list: bool = None
    ) -> RegisterSectionData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            section_data: RegisterSectionData = await self._update_register_section(
                register_id, section_id, tab_id, section_mnemonic, section_description,
                documents_required, no_of_verifications_required, auto_approval, is_list, session
            )
            return section_data

    async def _update_register_section(
        self,
        register_id: str,
        section_id: str,
        tab_id: str,
        section_mnemonic: str,
        section_description: str,
        documents_required: bool,
        no_of_verifications_required: int,
        auto_approval: bool,
        is_list: bool,
        session
    ) -> RegisterSectionData:
        section: G2PRegisterSection | None = await session.get(G2PRegisterSection, (register_id, section_id))
        if not section:
            raise ValueError(f"Section with register_id '{register_id}' and section_id '{section_id}' not found.")

        if tab_id is not None:
            await self._validate_register_tab(register_id, tab_id, session)
            section.tab_id = tab_id
        if section_mnemonic is not None:
            section.section_mnemonic = section_mnemonic
        if section_description is not None:
            section.section_description = section_description
        if documents_required is not None:
            section.documents_required = documents_required
        if no_of_verifications_required is not None:
            section.no_of_verifications_required = no_of_verifications_required
        if auto_approval is not None:
            section.auto_approval = auto_approval
        if is_list is not None:
            section.is_list = is_list

        await session.commit()
        await session.refresh(section)

        section_data: RegisterSectionData = RegisterSectionData(
            section_register_id=section.section_register_id,
            register_id=section.register_id,
            section_id=section.section_id,
            tab_id=section.tab_id,
            section_mnemonic=section.section_mnemonic,
            section_description=section.section_description,
            documents_required=section.documents_required,
            no_of_verifications_required=section.no_of_verifications_required,
            auto_approval=section.auto_approval,
            is_list=section.is_list,
            section_ui_schema=section.section_ui_schema
        )
        return section_data

    async def update_register_section_ui_schema(
        self,
        register_id: str,
        section_id: str,
        section_ui_schema: dict = None
    ) -> RegisterSectionData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            section_data: RegisterSectionData = await self._update_register_section_ui_schema(
                register_id, section_id, section_ui_schema, session
            )
            return section_data

    async def _update_register_section_ui_schema(
        self,
        register_id: str,
        section_id: str,
        section_ui_schema: dict,
        session
    ) -> RegisterSectionData:
        section: G2PRegisterSection | None = await session.get(G2PRegisterSection, (register_id, section_id))
        if not section:
            raise ValueError(f"Section with register_id '{register_id}' and section_id '{section_id}' not found.")

        section.section_ui_schema = section_ui_schema

        await session.commit()
        await session.refresh(section)

        section_data: RegisterSectionData = RegisterSectionData(
            section_register_id=section.section_register_id,
            register_id=section.register_id,
            section_id=section.section_id,
            tab_id=section.tab_id,
            section_mnemonic=section.section_mnemonic,
            section_description=section.section_description,
            documents_required=section.documents_required,
            no_of_verifications_required=section.no_of_verifications_required,
            auto_approval=section.auto_approval,
            is_list=section.is_list,
            section_ui_schema=section.section_ui_schema
        )
        return section_data

    async def search_in_a_register(self, register_id: str, search_text: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[SearchResultData], int]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self.validate_register_definition(register_id, session)
            search_results_list, total_items = await self._search_in_register(register_id, search_text, current_page, page_size, sort_by, filter_by, session)
            return search_results_list, total_items

    async def get_change_logs(self, subject_register_id: str, subject_record_id: str, tab_id: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[ChangeLogData], int]:
        """Get all change logs for a specific internal record and tab with pagination"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            await self.validate_register_definition(subject_register_id, session)
            change_logs_list, total_items = await self._fetch_change_logs(subject_register_id, subject_record_id, tab_id, current_page, page_size, sort_by, filter_by, session)
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
            await self.validate_change_log_section(change_log, session)
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

    async def validate_change_log_section(self, g2p_register_change_log: G2PRegisterChangeLog, session) -> None:
        g2p_register_section: G2PRegisterSection = (
            await session.execute(
                select(G2PRegisterSection).where(
                    G2PRegisterSection.section_id == g2p_register_change_log.section_id
                )
            )
        ).scalar()
        if not g2p_register_section:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.SECTION_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.SECTION_NOT_FOUND.value[0]
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
                    G2PRegisterDefinition.register_id == change_log.section_register_id
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
        if payload.change_payload:
            self._create_history_record(
                change_payload=payload.change_payload,
                change_log=change_log,
                history_schema_class=history_schema_class,
                history_class=history_class,
                session=session
            )
        else:
            for change_payload in payload.change_payload_array:
                self._create_history_record(
                    change_payload=change_payload,
                    change_log=change_log,
                    history_schema_class=history_schema_class,
                    history_class=history_class,
                    session=session
                )

    def _create_history_record(self, change_payload: dict, change_log: G2PRegisterChangeLog, history_schema_class, history_class, session) -> None:
        """Helper method to create and add a history record to the session"""
        # Serialize change log payload to history schema
        history_schema_instance = history_schema_class(**(change_payload or {}))

        # Build the history dict excluding None values from schema, then add base fields
        history_dict = {k: v for k, v in history_schema_instance.dict().items() if v is not None}
        history_dict["history_record_id"] = str(uuid.uuid4())
        history_dict["internal_record_id"] = change_payload.get("internal_record_id") if isinstance(change_payload, dict) else change_payload.internal_record_id
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
                    G2PRegisterDefinition.register_id == change_log.section_register_id
                )
            )
        ).scalar()
        module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
        register_class_prefix = "G2PRegister"
        implementation_class_name = f"{register_class_prefix}{register_definition.register_mnemonic}"
        register_class = getattr(module, implementation_class_name)

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

        if payload.change_payload:
            await self._create_or_update_register_record(
                change_payload=payload.change_payload,
                schema_class=schema_class,
                register_class=register_class,
                session=session
            )
        else:
            for change_payload in payload.change_payload_array:
                await self._create_or_update_register_record(
                    change_payload=change_payload,
                    schema_class=schema_class,
                    register_class=register_class,
                    session=session
                )

    async def _create_or_update_register_record(self, change_payload: dict, schema_class, register_class, session) -> None:
        """Helper method to create or update a register record"""
        # Serialize change log payload to register schema for validation
        register_schema_instance = schema_class(**(change_payload or {}))
        internal_record_id = change_payload.get("internal_record_id") if isinstance(change_payload, dict) else change_payload.internal_record_id

        existing = (
            await session.execute(
                select(register_class).where(
                    register_class.internal_record_id == internal_record_id
                )
            )
        ).scalar()

        if existing:
            for key, value in register_schema_instance.dict().items():
                # Only update values in change log payload
                if key in change_payload:
                    setattr(existing, key, value)
            setattr(existing, "last_approved_at", datetime.now())
            setattr(existing, "last_approved_by", "system")
        else:
            # Build the payload dict excluding None values from schema, then add base fields
            schema_dict = {k: v for k, v in register_schema_instance.dict().items() if v is not None}
            schema_dict["internal_record_id"] = internal_record_id
            schema_dict["functional_record_id"] = internal_record_id  # Use internal_record_id as functional_record_id
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

    async def validate_section(self, section_id: str, session) -> G2PRegisterSection:

        g2p_register_section: G2PRegisterSection =(
                await session.execute(
                select(G2PRegisterSection).where(
                    G2PRegisterSection.section_id == section_id
                )
            )
        ).scalar()
        if not g2p_register_section:
            raise ValueError(f"Section with ID {section_id} does not exist.")

        return g2p_register_section


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

    async def construct_change_log(self, change_log_request_payload: ChangeLogRequestPayload, g2p_register_section: G2PRegisterSection, source_partner_id: str = None) -> G2PRegisterChangeLog:
        change_log_id = str(uuid.uuid4())
        # Extract internal_record_id from change_payload if present, otherwise generate new UUID
        internal_record_id: str = None
        if change_log_request_payload.change_payload:
            internal_record_id = change_log_request_payload.change_payload.internal_record_id
        elif change_log_request_payload.change_payload_array and len(change_log_request_payload.change_payload_array) > 0:
            internal_record_id = change_log_request_payload.change_payload_array[0].internal_record_id
        internal_record_id = internal_record_id or str(uuid.uuid4())

        # Create the payload object
        change_log_payload_obj = G2PRegisterChangeLogPayload(
            change_log_id=change_log_id,
            change_payload=change_log_request_payload.change_payload.model_dump() if change_log_request_payload.change_payload else None,
            change_payload_array=[item.model_dump() for item in change_log_request_payload.change_payload_array] if change_log_request_payload.change_payload_array else None,
        )

        # Create the change log object
        g2p_register_change_log = G2PRegisterChangeLog(
            change_log_id=change_log_id,
            register_id=change_log_request_payload.register_id,
            tab_id=change_log_request_payload.tab_id,
            internal_record_id=internal_record_id,
            section_id=change_log_request_payload.section_id,
            section_register_id=change_log_request_payload.section_register_id,
            source_partner_id=source_partner_id or "system",
            created_by="system",  # TODO: Replace with actual user info
            created_at=func.now(),
            no_of_verifications_required=g2p_register_section.no_of_verifications_required,
            no_of_verifications_done=0,
            approval_status=ApprovalStatusEnum.PENDING.value,
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

    async def _fetch_changelog_summary_data(self, session) -> ChangeLogSummaryData:
        total_count: int = await self._count_all_changelogs(None, session)
        approved_count: int = await self._count_all_changelogs(ApprovalStatusEnum.APPROVED.value, session)
        pending_count: int = await self._count_all_changelogs(ApprovalStatusEnum.PENDING.value, session)

        changelog_summary_data: ChangeLogSummaryData = ChangeLogSummaryData(
            total_count=total_count,
            approved_count=approved_count,
            pending_count=pending_count
        )

        return changelog_summary_data

    async def _count_all_changelogs(self, approval_status: str | None, session) -> int:
        query = select(func.count()).select_from(G2PRegisterChangeLog)
        if approval_status is not None:
            query = query.where(G2PRegisterChangeLog.approval_status == approval_status)
        result = await session.execute(query)
        return result.scalar_one()

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

    async def _fetch_child_registers(self, master_register_id: str, session) -> list[ChildRegisterData]:
        child_register_definitions: list[G2PRegisterDefinition] = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.master_register_id == master_register_id
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

    async def _fetch_master_register(self, register_definition: G2PRegisterDefinition, session) -> RegisterData | None:
        master_register_id: str | None = register_definition.master_register_id
        if not master_register_id:
            return None

        master_register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == master_register_id
                )
            )
        ).scalars().first()

        if not master_register_definition:
            return None

        master_register_data: RegisterData = RegisterData(
            register_id=master_register_definition.register_id,
            register_mnemonic=master_register_definition.register_mnemonic,
            register_subject=master_register_definition.register_subject,
            register_description=master_register_definition.register_description,
            master_register_id=master_register_definition.master_register_id
        )
        return master_register_data

    async def _fetch_register_tabs(self, register_id: str, session) -> list[RegisterUITabData]:
        register_tabs: list[G2PRegisterUITab] = (
            await session.execute(
                select(G2PRegisterUITab).where(
                    G2PRegisterUITab.register_id == register_id
                ).order_by(G2PRegisterUITab.tab_order)
            )
        ).scalars().all()

        register_tabs_list: list[RegisterUITabData] = []
        for tab in register_tabs:
            tab_data: RegisterUITabData = RegisterUITabData(
                tab_id=tab.tab_id,
                register_id=tab.register_id,
                tab_label=tab.tab_label,
                tab_order=tab.tab_order
            )
            register_tabs_list.append(tab_data)

        return register_tabs_list

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
                tab_id=change_log.tab_id,
                internal_record_id=change_log.internal_record_id,
                section_id=change_log.section_id,
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

    async def get_number_of_pending_change_logs(self, subject_register_id: str, subject_record_id: str, tab_id: str) -> NumberOfPendingChangeLogsData:
        """Get the number of pending change logs for a given register, internal_record_id and tab_id"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            register_definition: G2PRegisterDefinition = (
                await session.execute(
                    select(G2PRegisterDefinition).where(
                        G2PRegisterDefinition.register_id == subject_register_id
                    )
                )
            ).scalar()
            if not register_definition:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0]
                )

            # Count pending change logs for the given internal_record_id and tab_id
            count_result = await session.execute(
                select(func.count()).select_from(G2PRegisterChangeLog).where(
                    (G2PRegisterChangeLog.register_id == subject_register_id) &
                    (G2PRegisterChangeLog.internal_record_id == subject_record_id) &
                    (G2PRegisterChangeLog.tab_id == tab_id) &
                    (G2PRegisterChangeLog.approval_status == ApprovalStatusEnum.PENDING.value)
                )
            )
            number_of_pending_change_logs = count_result.scalar_one()

            return NumberOfPendingChangeLogsData(
                subject_register_id=subject_register_id,
                subject_record_id=subject_record_id,
                tab_id=tab_id,
                number_of_pending_change_logs=number_of_pending_change_logs
            )

    async def get_number_of_cross_register_changes(self, subject_register_id: str, subject_record_id: str) -> NumberOfCrossRegisterChangesData:
        """Get the number of cross-register pending change logs by searching subject_record_id in search_text of G2PRegisterChangeLogPayload"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            register_definition: G2PRegisterDefinition = (
                await session.execute(
                    select(G2PRegisterDefinition).where(
                        G2PRegisterDefinition.register_id == subject_register_id
                    )
                )
            ).scalar()
            if not register_definition:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0]
                )

            # Count pending change logs where search_text contains subject_record_id
            # Join G2PRegisterChangeLog with G2PRegisterChangeLogPayload and search in search_text
            count_result = await session.execute(
                select(func.count()).select_from(G2PRegisterChangeLog).join(
                    G2PRegisterChangeLogPayload,
                    G2PRegisterChangeLog.change_log_id == G2PRegisterChangeLogPayload.change_log_id
                ).where(
                    (G2PRegisterChangeLog.approval_status == ApprovalStatusEnum.PENDING.value) &
                    (G2PRegisterChangeLogPayload.search_text.ilike(f"%{subject_record_id}%"))
                )
            )
            number_of_cross_register_changes = count_result.scalar_one()

            return NumberOfCrossRegisterChangesData(
                subject_register_id=subject_register_id,
                subject_record_id=subject_record_id,
                number_of_cross_register_changes=number_of_cross_register_changes
            )

    async def get_cross_register_changes(self, subject_register_id: str, subject_record_id: str) -> list[CrossRegisterChangeLogData]:
        """Get the list of cross-register pending change logs by searching subject_record_id in search_text of G2PRegisterChangeLogPayload"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            register_definition: G2PRegisterDefinition = (
                await session.execute(
                    select(G2PRegisterDefinition).where(
                        G2PRegisterDefinition.register_id == subject_register_id
                    )
                )
            ).scalar()
            if not register_definition:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0]
                )

            # Fetch pending change logs where search_text contains subject_record_id
            # Join G2PRegisterChangeLog with G2PRegisterChangeLogPayload, G2PRegisterDefinition, and G2PRegisterUITab
            result = await session.execute(
                select(
                    G2PRegisterChangeLog,
                    G2PRegisterDefinition.register_mnemonic,
                    G2PRegisterUITab.tab_label
                ).join(
                    G2PRegisterChangeLogPayload,
                    G2PRegisterChangeLog.change_log_id == G2PRegisterChangeLogPayload.change_log_id
                ).join(
                    G2PRegisterDefinition,
                    G2PRegisterChangeLog.register_id == G2PRegisterDefinition.register_id
                ).join(
                    G2PRegisterUITab,
                    G2PRegisterChangeLog.tab_id == G2PRegisterUITab.tab_id
                ).where(
                    (G2PRegisterChangeLog.approval_status == ApprovalStatusEnum.PENDING.value) &
                    (G2PRegisterChangeLogPayload.search_text.ilike(f"%{subject_record_id}%"))
                ).order_by(G2PRegisterChangeLog.created_at.desc())
            )
            rows = result.all()

            cross_register_changes: list[CrossRegisterChangeLogData] = []
            for row in rows:
                change_log = row[0]
                register_mnemonic = row[1]
                tab_label = row[2]
                cross_register_changes.append(CrossRegisterChangeLogData(
                    change_log_id=change_log.change_log_id,
                    register_id=change_log.register_id,
                    register_mnemonic=register_mnemonic,
                    tab_id=change_log.tab_id,
                    tab_label=tab_label,
                    internal_record_id=change_log.internal_record_id,
                    section_id=change_log.section_id,
                    source_partner_id=change_log.source_partner_id,
                    created_by=change_log.created_by,
                    created_at=change_log.created_at.isoformat() if change_log.created_at else None,
                    no_of_verifications_required=change_log.no_of_verifications_required,
                    no_of_verifications_done=change_log.no_of_verifications_done,
                    approval_status=change_log.approval_status,
                    approved_by=change_log.approved_by,
                    approved_at=change_log.approved_at.isoformat() if change_log.approved_at else None
                ))

            return cross_register_changes

    async def _fetch_change_logs(self, subject_register_id: str, subject_record_id: str, tab_id: str, current_page: int, page_size: int, sort_by: str, filter_by: dict, session) -> tuple[list[ChangeLogData], int]:
        """Helper method to fetch all change logs for a specific internal record and tab with pagination"""
        # Build base query
        base_query = select(G2PRegisterChangeLog, G2PRegisterChangeLogPayload).join(
            G2PRegisterChangeLogPayload,
            G2PRegisterChangeLog.change_log_id == G2PRegisterChangeLogPayload.change_log_id
        ).where(
            (G2PRegisterChangeLog.register_id == subject_register_id) &
            (G2PRegisterChangeLog.internal_record_id == subject_record_id) &
            (G2PRegisterChangeLog.tab_id == tab_id)
        ).order_by(G2PRegisterChangeLog.created_at.desc())

        # Get total count
        count_result = await session.execute(select(func.count()).select_from(G2PRegisterChangeLog).where(
            (G2PRegisterChangeLog.register_id == subject_register_id) &
            (G2PRegisterChangeLog.internal_record_id == subject_record_id) &
            (G2PRegisterChangeLog.tab_id == tab_id)
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
                tab_id=change_log.tab_id,
                internal_record_id=change_log.internal_record_id,
                section_id=change_log.section_id,
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
            tab_id=change_log.tab_id,
            internal_record_id=change_log.internal_record_id,
            section_id=change_log.section_id,
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
                    section_id=verification.section_id,
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
                section_id=change_log.section_id,
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
                section_id=verification.section_id,
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
                section_register_id=section.section_register_id,
                register_id=section.register_id,
                section_id=section.section_id,
                tab_id=section.tab_id,
                section_mnemonic=section.section_mnemonic,
                section_description=section.section_description,
                documents_required=section.documents_required,
                no_of_verifications_required=section.no_of_verifications_required,
                auto_approval=section.auto_approval,
                is_list=section.is_list,
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
            section_register_id=section.section_register_id,
            register_id=section.register_id,
            section_id=section.section_id,
            tab_id=section.tab_id,
            section_mnemonic=section.section_mnemonic,
            section_description=section.section_description,
            documents_required=section.documents_required,
            no_of_verifications_required=section.no_of_verifications_required,
            auto_approval=section.auto_approval,
            is_list=section.is_list,
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
