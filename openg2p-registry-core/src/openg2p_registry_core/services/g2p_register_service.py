import logging
import uuid
import importlib
from datetime import datetime, date
from fastapi_cache.decorator import cache

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from openg2p_registry_core.schemas import ChangeRequestRequestPayload
from sqlalchemy.orm import Session
from sqlalchemy import func, insert, select, inspect, Date as SQLDate, or_
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..helpers import MinioClient

from ..cache import metadata_key_builder

from ..models import (
    G2PRegisterChangeRequest, G2PRegisterChangeRequestPayload, G2PRegisterChangeRequestDocument,
    G2PRegisterDefinition, G2PRegisterSection, G2PRegisterVerification, ApprovalStatusEnum,
    DeduplicationRegisterResult, DeduplicationChangerequestResult, G2PRegisterSchema,
    G2PRegisterSection, G2PRegisterUITab, RegisterPurposeEnum, ChangeRequestSourceEnum,
    G2PRegisterSectionDocument, G2PRegisterDocumentHistory,
    G2PRegistryConfiguration, G2PRegistryDocument
)
from ..schemas import (
    ChangeRequestRequestPayload, RegisterSummaryData, ChangeRequestSummaryData, RegisterData, ChildRegisterData,
    RegisterUITabData, SearchResultData, ChangeRequestSearchResultData, NumberOfVersionsData,
    RecordHistoryData, RecordHistoryListData, VersionDatesData, VersionForDateData, VersionsForDateData,
    NumberOfPendingChangeRequestsData, NumberOfCrossRegisterChangesData,
    CrossRegisterChangeRequestData, CrossRegisterChangesData, DeepSearchResultData,
    ChangeRequestData, ChangeRequestsData, ChangeRequestFlattenedData, RecordData,
    VerificationData, VerificationsData, AddVerificationPayload,
    DeduplicationRegisterResultsData, DeduplicationChangerequestResultsData,
    DeduplicationRegisterResultData, DeduplicationChangerequestResultData,
    RegisterSchemaData, RegisterSectionData, DisplayField,
    UploadedDocumentData, UploadDocumentsResponseData,
    RegistryConfigurationData, EarliestPendingChangeRequestData,
    ChangePayload, EditActionEnum, ChangeRequestDocumentsData, SectionDocumentData, SectionDocumentsData
)
from ..config import Settings
from ..errors import G2PRegistryErrorCodes, G2PRegistryException
from .filter_builder import FilterBuilder

_logger = logging.getLogger('g2p-register-service')
_engine = dbengine.get()
_config = Settings.get_config(strict=False)

class G2PRegisterService(BaseService):


    @cache(expire=_config.cache_expires_in_seconds, key_builder=metadata_key_builder)
    async def _get_register_definition(self, register_id: str, session):
        return await session.get(G2PRegisterDefinition, register_id)

    @cache(expire=_config.cache_expires_in_seconds, key_builder=metadata_key_builder)
    async def _get_section(self, section_id: str, session):
        return await session.get(G2PRegisterSection, section_id)

    @cache(expire=_config.cache_expires_in_seconds, key_builder=metadata_key_builder)
    async def _get_tab(self, tab_id: str, session):
        return await session.get(G2PRegisterUITab, tab_id)

    async def create_change_request(self, change_request_request_payload: ChangeRequestRequestPayload, source_partner_id: str = None, application_id: str = None):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:

            g2p_register_definition: G2PRegisterDefinition = await self.validate_register_definition(change_request_request_payload.register_id, session)
            g2p_register_section: G2PRegisterSection = await self.validate_section(change_request_request_payload.section_id, session)

            # Extract internal_record_id from change_payload if present
            # Note: For new record creation, internal_record_id may be a new UUID that doesn't exist yet
            # We don't validate internal_record_id existence here - it will be created when the change request is approved

            g2p_register_change_request: G2PRegisterChangeRequest = await self.construct_change_request(change_request_request_payload, g2p_register_section, source_partner_id, application_id)

            session.add(g2p_register_change_request)
            # Add the payload object if it exists
            if hasattr(g2p_register_change_request, '_payload_to_add'):
                session.add(g2p_register_change_request._payload_to_add)

            # Add documents if provided
            if change_request_request_payload.documents:
                for doc in change_request_request_payload.documents:
                    change_request_doc = G2PRegisterChangeRequestDocument(
                        change_request_id=g2p_register_change_request.change_request_id,
                        document_label=doc.document_label,
                        document_store_id=doc.document_store_id
                    )
                    session.add(change_request_doc)

            await session.commit()
            # Refresh to get any DB defaults
            await session.refresh(g2p_register_change_request)

            return g2p_register_change_request

    async def get_register_summary_data(self) -> list[RegisterSummaryData]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            register_summary_data_list: list[RegisterSummaryData] = await self._fetch_register_summary_data(session)
            return register_summary_data_list

    async def get_change_request_summary_data(self) -> ChangeRequestSummaryData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            change_request_summary_data: ChangeRequestSummaryData = await self._fetch_change_request_summary_data(session)
            return change_request_summary_data

    async def get_all_registers(self) -> list[RegisterData]:
        print("Fetching all registers for you", dbengine.get())
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
    
    async def deep_search_in_a_register(
        self, register_id: str, search_text: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None
    ) -> tuple[list[DeepSearchResultData], int]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self.validate_register_definition(register_id, session)
            deep_search_results_list, total_items = await self._deep_search_in_register(register_id, search_text, current_page, page_size, sort_by, filter_by, session)
            return deep_search_results_list, total_items

    async def get_change_requests(self, subject_register_id: str, subject_record_id: str, tab_id: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[ChangeRequestData], int]:
        """Get all change requests for a specific internal record and tab with pagination"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            await self.validate_register_definition(subject_register_id, session)
            change_requests_list, total_items = await self._fetch_change_requests(subject_register_id, subject_record_id, tab_id, current_page, page_size, sort_by, filter_by, session)
            return change_requests_list, total_items

    async def get_change_request(self, change_request_id: str) -> ChangeRequestData:
        """Get a single change request by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            change_request_data: ChangeRequestData = await self._fetch_change_request(change_request_id, session)
            return change_request_data

    async def get_change_requests_flattened(self, subject_register_id: str, subject_record_id: str, tab_id: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[ChangeRequestFlattenedData], int]:
        """Get all change requests for a specific internal record and tab with flattened change_payload fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            await self.validate_register_definition(subject_register_id, session)
            change_requests_list, total_items = await self._fetch_change_requests_flattened(subject_register_id, subject_record_id, tab_id, current_page, page_size, sort_by, filter_by, session)
            return change_requests_list, total_items

    async def approve_change_request(self, change_request_id: str):
        # if change_request.change_request_source is APPLICATION, loop through all change requests for the application and approve them
        # if change_request.change_request_source is DIRECT, just approve the single change request
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            change_request = await self.validate_change_request_exists(change_request_id, session)
            if change_request.change_request_source == ChangeRequestSourceEnum.APPLICATION.value:
                change_requests = await self._fetch_change_requests_for_application(change_request.application_id, session)
                for change_request in change_requests:
                    await self.approve_single_change_request(change_request.change_request_id, session)
                    _logger.info(f"Approved change request: {change_request.change_request_id}")
            else:
                await self.approve_single_change_request(change_request_id, session)
                _logger.info(f"Approved change request: {change_request_id}")    

            await session.commit()
            await session.refresh(change_request)
            return change_request              
       

    async def approve_single_change_request(self, change_request_id: str, session):
        # Validate change request exists and is pending approval
        change_request = await self.validate_change_request_exists(change_request_id, session)
        # Mark change request as approved
        change_request.approval_status = ApprovalStatusEnum.APPROVED.value
        change_request.approved_by = "system" # TODO: Replace with actual user info
        change_request.approved_at = datetime.now()
        session.add(change_request)
        
        _logger.info(f"Validating change request for approval: {change_request}")
        g2p_register_section = await self.validate_change_request_section(change_request, session)
        # Validate whether verifications are done
        await self.validate_change_request_verifications(change_request, session)
        # Ensure there are no earlier change requests for the internal_record_id pending approval
        await self.validate_change_request_sequence(change_request, session)
        # In case of approval, insert data into register_history
        await self.insert_into_register_history(change_request, session)
        # Upsert data into register
        await self.insert_into_register(change_request, session)
        # Handle documents if section.documents_required is True
        if g2p_register_section and g2p_register_section.documents_required:
            await self._handle_documents_on_approval(change_request, g2p_register_section, session)

        return change_request
            
    async def _fetch_change_requests_for_application(self, application_id: str, session) -> list[G2PRegisterChangeRequest]:
        result = await session.execute(
            select(G2PRegisterChangeRequest).where(
                G2PRegisterChangeRequest.application_id == application_id
            )
        )
        return result.scalars().all()
    
    async def reject_change_request(self, change_request_id: str, reason: str):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate change request exists and is pending approval
            change_request = await self.validate_change_request_exists(change_request_id, session)
            _logger.info(f"Validated change request for rejection: {change_request}")
            # Mark change request as rejected
            change_request.approval_status = ApprovalStatusEnum.REJECTED.value
            change_request.approved_by = "system" # TODO: Replace with actual user info
            change_request.approved_at = datetime.now()
            change_request.rejection_reason = reason
            await session.commit()
            await session.refresh(change_request)
            return change_request

    async def validate_change_request_section(self, g2p_register_change_request: G2PRegisterChangeRequest, session) -> G2PRegisterSection:
        g2p_register_section: G2PRegisterSection = (
            await session.execute(
                select(G2PRegisterSection).where(
                    G2PRegisterSection.section_id == g2p_register_change_request.section_id
                )
            )
        ).scalar()
        if not g2p_register_section:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.SECTION_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.SECTION_NOT_FOUND.value[0]
            )
        # Note: internal_record_id is already set during change request creation in construct_change_request
        # Do not generate a new one here during approval
        return g2p_register_section

        
    async def validate_change_request_exists(self, change_request_id: str, session) -> G2PRegisterChangeRequest:
        _logger.info(f"Validating change request exists for ID: {change_request_id}")
        change_request: G2PRegisterChangeRequest = (
            await session.execute(
                select(G2PRegisterChangeRequest).where(
                    G2PRegisterChangeRequest.change_request_id == change_request_id
                )
            )
        ).scalar()
        if not change_request:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_FOUND.value[0]
            )
        if change_request.approval_status != ApprovalStatusEnum.PENDING.value:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_IN_PENDING_STATE.value[1],
                message=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_IN_PENDING_STATE.value[0]
            )
        return change_request

    async def validate_change_request_verifications(self, change_request: G2PRegisterChangeRequest, session) -> None:
        # Count only approved verifications
        approved_verifications_count = (
            await session.execute(
                select(func.count()).select_from(G2PRegisterVerification).where(
                    G2PRegisterVerification.change_request_id == change_request.change_request_id,
                    G2PRegisterVerification.is_approved == True
                )
            )
        ).scalar_one()
        if approved_verifications_count < (change_request.no_of_verifications_required or 0):
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.VERIFICATIONS_PENDING.value[1],
                message=G2PRegistryErrorCodes.VERIFICATIONS_PENDING.value[0]
            )

    async def validate_change_request_sequence(self, change_request: G2PRegisterChangeRequest, session) -> None:
        earlier_pending = (
            await session.execute(
                select(G2PRegisterChangeRequest).where(
                    G2PRegisterChangeRequest.internal_record_id == change_request.internal_record_id,
                    G2PRegisterChangeRequest.approval_status == "PENDING",
                    G2PRegisterChangeRequest.created_at < change_request.created_at,
                )
            )
        ).scalars().first()
        if earlier_pending:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1],
                message="There are earlier pending change requests for this record"
            )

    async def insert_into_register_history(self, change_request: G2PRegisterChangeRequest, session) -> None:
        # Resolve history model class dynamically based on register mnemonic
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == change_request.section_register_id
                )
            )
        ).scalar()
        if not register_definition:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0]
            )
        if register_definition.register_purpose == RegisterPurposeEnum.PROGRAM_APPLICATION.value:
            # No history for program applications
            return
        
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
            select(G2PRegisterChangeRequestPayload).where(
                G2PRegisterChangeRequestPayload.change_request_id == change_request.change_request_id
            )
        )
        payload = payload_result.scalar()
        # change_payload is now always a list
        if payload.change_payload:
            for change_payload in payload.change_payload:
                self._create_history_record(
                    change_payload=change_payload,
                    change_request=change_request,
                    history_schema_class=history_schema_class,
                    history_class=history_class,
                    session=session
                )

    def _convert_date_strings_to_objects(self, data_dict: dict, model_class) -> dict:
        """Helper method to convert date strings to date objects for SQLAlchemy Date columns"""
        # Get the model's column information
        mapper = inspect(model_class)
        converted_dict = data_dict.copy()
        
        for key, value in converted_dict.items():
            if value is None:
                continue
            # Check if the column is a Date type
            if key in mapper.columns:
                column = mapper.columns[key]
                # Check if column type is SQLAlchemy Date type
                if isinstance(column.type, SQLDate):
                    # If value is a string, try to convert it to a date object
                    if isinstance(value, str):
                        try:
                            converted_dict[key] = datetime.strptime(value, '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            # If parsing fails, keep the original value
                            pass
                    elif isinstance(value, datetime):
                        # If it's a datetime, convert to date
                        converted_dict[key] = value.date()
        
        return converted_dict

    def _create_history_record(self, change_payload: ChangePayload, change_request: G2PRegisterChangeRequest, history_schema_class, history_class, session) -> None:
        """Helper method to create and add a history record to the session"""
        # Serialize change request payload to history schema
        history_schema_instance = history_schema_class(**(change_payload or {}))

        # Build the history dict excluding None values from schema, then add base fields
        history_dict = {k: v for k, v in history_schema_instance.dict().items() if v is not None}
        history_dict["history_record_id"] = str(uuid.uuid4())
        history_dict["internal_record_id"] = change_payload.get("internal_record_id")
        history_dict["tab_id"] = change_request.tab_id
        history_dict["section_id"] = change_request.section_id
        history_dict["application_id"] = change_request.application_id
        history_dict["change_request_source"] = change_request.change_request_source
        history_dict["is_primary_section"] = change_request.is_primary_section

        history_dict["change_request_id"] = change_request.change_request_id
        history_dict["created_at"] = change_request.created_at
        history_dict["created_by"] = change_request.created_by
        history_dict["approved_at"] = change_request.approved_at
        history_dict["approved_by"] = change_request.approved_by
        
        # Convert date strings to date objects before creating the instance
        history_dict = self._convert_date_strings_to_objects(history_dict, history_class)
        
        history_instance = history_class(**history_dict)
        session.add(history_instance)


    async def insert_into_register(self, change_request: G2PRegisterChangeRequest, session) -> None:
        # Resolve register model class dynamically based on register mnemonic
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == change_request.section_register_id
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
            select(G2PRegisterChangeRequestPayload).where(
                G2PRegisterChangeRequestPayload.change_request_id == change_request.change_request_id
            )
        )
        payload = payload_result.scalar()

        # change_payload is now always a list
        if payload.change_payload:
            for change_payload in payload.change_payload:
                await self._create_or_update_register_record(
                    change_request=change_request,
                    change_payload=change_payload,
                    schema_class=schema_class,
                    register_class=register_class,
                    session=session
                )

    async def _create_or_update_register_record(self, change_request: G2PRegisterChangeRequest, change_payload: ChangePayload,  schema_class, register_class, session) -> None:
        """Helper method to create or update a register record"""
        # Serialize change request payload to register schema for validation
        register_schema_instance = schema_class(**(change_payload or {}))
        
        existing = (
            await session.execute(
                select(register_class).where(
                    register_class.internal_record_id == change_payload.get("internal_record_id")
                )
            )
        ).scalar()

        if change_payload.get("edit_action") == EditActionEnum.UPDATE.value and existing:
            mapper = inspect(register_class)
            for key, value in register_schema_instance.dict().items():
                # Only update values in change request payload
                if key in change_payload:
                    # Convert date strings to date objects if needed
                    if value is not None and key in mapper.columns:
                        column = mapper.columns[key]
                        if isinstance(column.type, SQLDate):
                            if isinstance(value, str):
                                try:
                                    value = datetime.strptime(value, '%Y-%m-%d').date()
                                except (ValueError, TypeError):
                                    pass
                            elif isinstance(value, datetime):
                                value = value.date()
                    setattr(existing, key, value)
            setattr(existing, "last_approved_at", datetime.now())
            setattr(existing, "last_approved_by", "system")
        elif change_payload.get("edit_action") == EditActionEnum.ADD.value:
            # Build the payload dict excluding None values from schema, then add base fields
            schema_dict = {k: v for k, v in register_schema_instance.dict().items() if v is not None}
            schema_dict["functional_record_id"] = change_payload.get("functional_record_id") 
            schema_dict["created_by"] = change_request.created_by
            schema_dict["created_at"] = change_request.created_at
            schema_dict["last_approved_at"] = change_request.approved_at
            schema_dict["last_approved_by"] = "system"
            
            # Convert date strings to date objects before creating the instance
            schema_dict = self._convert_date_strings_to_objects(schema_dict, register_class)
            
            new_instance = register_class(**schema_dict)
            session.add(new_instance)
        elif change_payload.get("edit_action") == EditActionEnum.DELETE.value and existing:
            await session.delete(existing)
        elif change_payload.get("edit_action") == EditActionEnum.NO_CHANGE.value and existing:
            _logger.info(f"No change action for change request '{change_request.change_request_id}', skipping register update.")
        else:
            _logger.error(f"Unknown edit action '{change_payload.get('edit_action')}' for change request '{change_request.change_request_id}'")
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.UNKNOWN_CHANGE_REQUEST_ACTION.value[1],
                message=G2PRegistryErrorCodes.UNKNOWN_CHANGE_REQUEST_ACTION.value[0]
            )
                
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

    async def validate_tab(self, tab_id: str, session) -> G2PRegisterUITab:
        g2p_register_tab: G2PRegisterUITab = (
            await session.execute(
                select(G2PRegisterUITab).where(
                    G2PRegisterUITab.tab_id == tab_id
                )
            )
        ).scalar()
        if not g2p_register_tab:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.TAB_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.TAB_NOT_FOUND.value[0]
            )

        return g2p_register_tab

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

    async def construct_change_request(self, change_request_request_payload: ChangeRequestRequestPayload, g2p_register_section: G2PRegisterSection, source_partner_id: str = None, application_id: str = None) -> G2PRegisterChangeRequest:
        change_request_id = str(uuid.uuid4())
        # Extract internal_record_id if present, otherwise generate new UUID
        internal_record_id: str = None
        if change_request_request_payload.change_payload and len(change_request_request_payload.change_payload) > 0:
            internal_record_id = change_request_request_payload.internal_record_id
        internal_record_id = internal_record_id or str(uuid.uuid4())

        # Loop through change_payload to set internal_record_id for each item if not already set only if edit_action is ADD
        if change_request_request_payload.change_payload:
            for item in change_request_request_payload.change_payload:
                if not item.internal_record_id and item.edit_action == EditActionEnum.ADD:
                    item.internal_record_id = str(uuid.uuid4())

        # Create the payload object - change_payload is now always a list
        change_request_payload_obj = G2PRegisterChangeRequestPayload(
            change_request_id=change_request_id,
            change_payload=[item.model_dump() for item in change_request_request_payload.change_payload] if change_request_request_payload.change_payload else [],
        )

        # Determine change request source based on application_id
        change_request_source = ChangeRequestSourceEnum.APPLICATION.value if application_id else ChangeRequestSourceEnum.DIRECT.value

        # Create the change request object
        g2p_register_change_request = G2PRegisterChangeRequest(
            change_request_id=change_request_id,
            register_id=change_request_request_payload.register_id,
            tab_id=change_request_request_payload.tab_id,
            internal_record_id=internal_record_id,
            section_id=change_request_request_payload.section_id,
            section_register_id=change_request_request_payload.section_register_id,
            source_partner_id=source_partner_id or "system",
            change_request_source=change_request_source,
            application_id=application_id,
            created_by="system",  # TODO: Replace with actual user info
            created_at=datetime.now(),
            no_of_verifications_required=g2p_register_section.no_of_verifications_required,
            no_of_verifications_done=0,
            approval_status=ApprovalStatusEnum.PENDING.value,
        )

        # Add both objects to session so they're persisted together
        # The payload will be added when the change request is added
        g2p_register_change_request._payload_to_add = change_request_payload_obj
        return g2p_register_change_request

    async def _fetch_register_summary_data(self, session) -> list[RegisterSummaryData]:
        register_definitions: list[G2PRegisterDefinition] = (
            await session.execute(
                select(G2PRegisterDefinition)
                .where(G2PRegisterDefinition.register_purpose != RegisterPurposeEnum.TABLE.value)
            )
        ).scalars().all()

        register_summary_data_list: list[RegisterSummaryData] = []

        for register_definition in register_definitions:
            total_record_count: int = await self._count_records_for_register(register_definition, session)

            register_summary_data: RegisterSummaryData = RegisterSummaryData(
                register_id=register_definition.register_id,
                register_mnemonic=register_definition.register_mnemonic,
                register_subject=register_definition.register_subject,
                has_image=register_definition.has_image,
                register_icon=register_definition.register_icon,
                total_record_count=total_record_count
            )
            register_summary_data_list.append(register_summary_data)

        return register_summary_data_list

    async def _fetch_change_request_summary_data(self, session) -> ChangeRequestSummaryData:
        total_count: int = await self._count_all_change_requests(None, session)
        approved_count: int = await self._count_all_change_requests(ApprovalStatusEnum.APPROVED.value, session)
        pending_count: int = await self._count_all_change_requests(ApprovalStatusEnum.PENDING.value, session)

        change_request_summary_data: ChangeRequestSummaryData = ChangeRequestSummaryData(
            total_count=total_count,
            approved_count=approved_count,
            pending_count=pending_count
        )

        return change_request_summary_data

    async def _count_all_change_requests(self, approval_status: str | None, session) -> int:
        query = select(func.count()).select_from(G2PRegisterChangeRequest)
        if approval_status is not None:
            query = query.where(G2PRegisterChangeRequest.approval_status == approval_status)
        result = await session.execute(query)
        return result.scalar_one()

    async def _count_change_requests_for_register(self, register_id: str, approval_status: str | None, session) -> int:
        query = select(func.count()).select_from(G2PRegisterChangeRequest).where(
            G2PRegisterChangeRequest.register_id == register_id
        )
        if approval_status is not None:
            query = query.where(G2PRegisterChangeRequest.approval_status == approval_status)

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
            await session.execute(
                select(G2PRegisterDefinition)
                .where(G2PRegisterDefinition.register_purpose != RegisterPurposeEnum.TABLE.value)
                .order_by(G2PRegisterDefinition.register_rank)
            )
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
    
    async def _deep_search_in_register(self, register_id: str, search_text: str, current_page: int, page_size: int, sort_by: str, filter_by: dict, session) -> tuple[list[DeepSearchResultData], int]:
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
        
        # Build search query
        search_query: str = f"%{search_text}%"

        # Base filter: search_text applied on implementation_class.search_text
        filter_conditions: list = [implementation_class.search_text.ilike(search_query)]

        # Additional filters if provided
        if filter_by:
            # Assuming a FilterBuilder exists for consistency, but focusing only on filter_by structure as in _search_in_register
            filter_builder = FilterBuilder([])  # No schema used for deep search
            try:
                user_filter_conditions = filter_builder.build_conditions(filter_by, implementation_class)
                filter_conditions.extend(user_filter_conditions)
            except ValueError as validation_error:
                _logger.warning(f"Filter validation error: {validation_error}")
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.INVALID_REQUEST.value[1],
                    message=str(validation_error)
                )

        # Sorting
        order_by_clause = None
        if sort_by:
            # Sort descending if startswith '-', else ascending
            column_name = sort_by.lstrip('-')
            sort_column = getattr(implementation_class, column_name, None)
            if sort_column is not None:
                if sort_by.startswith('-'):
                    order_by_clause = sort_column.desc()
                else:
                    order_by_clause = sort_column.asc()

        # Total count
        total_query = select(implementation_class).filter(*filter_conditions)
        total_count = (await session.execute(total_query)).scalars().unique().all()
        total_count = len(total_count)

        # Pagination
        offset = (current_page - 1) * page_size

        # Query records
        query = select(implementation_class).filter(*filter_conditions)
        if order_by_clause is not None:
            query = query.order_by(order_by_clause)
        query = query.offset(offset).limit(page_size)

        results = (await session.execute(query)).scalars().all()

        # Build DeepSearchResultData list
        deep_search_results_list: list[DeepSearchResultData] = []
        for record in results:
            # Convert all datetime fields to ISO format strings for pydantic compatibility
            if hasattr(record, "model_dump"):
                data_dict = record.model_dump(exclude_unset=False, by_alias=False)
            elif hasattr(record, "dict"):
                data_dict = record.dict(exclude_unset=False, by_alias=False)
            else:
                data_dict = dict(record.__dict__)
            # Remove private attributes
            data_dict = {k: v for k, v in data_dict.items() if not k.startswith("_")}
            # Convert all datetime and date values to ISO strings where necessary
            for k, v in list(data_dict.items()):
                # Import here to avoid circular deps
                import datetime
                if isinstance(v, datetime.datetime) or isinstance(v, datetime.date):
                    data_dict[k] = v.isoformat()
            deep_search_results_list.append(DeepSearchResultData(**data_dict))

        return deep_search_results_list, total_count


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

        # Get MinIO client for generating presigned URLs
        from ..helpers import MinioClient
        minio_client: MinioClient = MinioClient.get_component()

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

            # Generate presigned URL for record image if it exists
            record_image_url = None
            if hasattr(result, 'image') and result.image:
                record_image_url = minio_client.get_url(object_name=result.image)

            # Create SearchResultData object
            search_result_data: SearchResultData = SearchResultData(
                internal_record_id=result.internal_record_id,
                functional_record_id=result.functional_record_id,
                link_internal_record_id=result.link_internal_record_id,
                foundational_id=result.foundational_id,
                link_foundational_id=result.link_foundational_id,
                record_name=result.record_name,
                record_image_url=record_image_url,
                created_by=result.created_by,
                created_at=str(result.created_at.isoformat()) if result.created_at and hasattr(result.created_at, 'isoformat') else None,
                last_approved_at=str(result.last_approved_at.isoformat()) if result.last_approved_at and hasattr(result.last_approved_at, 'isoformat') else None,
                last_approved_by=result.last_approved_by,
                display_fields=display_fields_list if display_fields_list else None
            )
            search_results_list.append(search_result_data)

        return search_results_list, total_items

    async def search_in_change_request(self, search_text: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[ChangeRequestSearchResultData], int]:
        """Search in change requests using search_text field with pagination"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            search_results, total_items = await self._search_in_change_request(search_text, current_page, page_size, sort_by, filter_by, session)
            return search_results, total_items

    async def _search_in_change_request(self, search_text: str, current_page: int, page_size: int, sort_by: str, filter_by: dict, session) -> tuple[list[ChangeRequestSearchResultData], int]:
        """Helper method to search in change requests with pagination"""
        search_query = f"%{search_text}%"

        # Build base query
        base_query = select(G2PRegisterChangeRequest, G2PRegisterChangeRequestPayload).join(
            G2PRegisterChangeRequestPayload,
            G2PRegisterChangeRequest.change_request_id == G2PRegisterChangeRequestPayload.change_request_id
        ).where(
            G2PRegisterChangeRequestPayload.search_text.ilike(search_query)
        )

        # Get total count
        count_result = await session.execute(select(func.count()).select_from(G2PRegisterChangeRequest).join(
            G2PRegisterChangeRequestPayload,
            G2PRegisterChangeRequest.change_request_id == G2PRegisterChangeRequestPayload.change_request_id
        ).where(
            G2PRegisterChangeRequestPayload.search_text.ilike(search_query)
        ))
        total_items = count_result.scalar() or 0

        # Apply pagination
        offset = (current_page - 1) * page_size
        query = base_query.offset(offset).limit(page_size)

        result = await session.execute(query)
        search_results = result.all()

        search_results_list: list[ChangeRequestSearchResultData] = []

        # Convert ORM objects to ChangeRequestSearchResultData while still in session context
        for change_request, payload in search_results:
            # Convert datetime objects to strings
            created_at_str = str(change_request.created_at.isoformat()) if change_request.created_at and hasattr(change_request.created_at, 'isoformat') else None
            approved_at_str = str(change_request.approved_at.isoformat()) if change_request.approved_at and hasattr(change_request.approved_at, 'isoformat') else None

            # Get change_payload from the payload object
            change_payload = payload.change_payload if payload else None

            # Get register mnemonic from the register object
            register_metadata = await self._get_register_definition(change_request.register_id, session)
            section_metadata = await self._get_section(change_request.section_id, session)
            tab_metadata = await self._get_tab(change_request.tab_id, session)

            if isinstance(register_metadata, dict):
                register_metadata = G2PRegisterDefinition(**register_metadata)
            if isinstance(section_metadata, dict):
                section_metadata = G2PRegisterSection(**section_metadata)
            if isinstance(tab_metadata, dict):
                tab_metadata = G2PRegisterUITab(**tab_metadata)

            # Create ChangeRequestSearchResultData object
            change_request_search_result: ChangeRequestSearchResultData = ChangeRequestSearchResultData(
                change_request_id=change_request.change_request_id,
                register_id=change_request.register_id,
                register_mnemonic=register_metadata.register_mnemonic,
                tab_id=change_request.tab_id,
                tab_label=tab_metadata.tab_label,
                internal_record_id=change_request.internal_record_id,
                section_id=change_request.section_id,
                section_mnemonic=section_metadata.section_mnemonic,
                source_partner_id=change_request.source_partner_id,
                created_by=change_request.created_by,
                created_at=created_at_str,
                no_of_verifications_required=change_request.no_of_verifications_required,
                no_of_verifications_done=change_request.no_of_verifications_done,
                approval_status=change_request.approval_status,
                approved_by=change_request.approved_by,
                approved_at=approved_at_str,
                change_payload=change_payload
            )
            search_results_list.append(change_request_search_result)

        return search_results_list, total_items

    async def get_number_of_versions(self, register_id: str, internal_record_id: str, tab_id: str) -> NumberOfVersionsData:
        """Get the number of versions (history records) for a given register, internal_record_id and tab_id"""
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
                tab_id=tab_id,
                number_of_versions=number_of_versions,
                last_updated_by=last_updated_by,
                last_updated_at=last_updated_at,
                last_approved_by=last_approved_by,
                last_approved_at=last_approved_at
            )

    async def get_record_history(self, register_id: str, internal_record_id: str, tab_id: str) -> RecordHistoryListData:
        """Get the history records for a given register, internal_record_id and tab_id"""
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

            # Dynamically resolve history model class based on register mnemonic
            module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
            history_class_prefix = "G2PRegisterHistory"
            history_class_name = f"{history_class_prefix}{register_definition.register_mnemonic}"
            history_class = getattr(module, history_class_name)

            # Fetch all history records for the given internal_record_id, ordered by approved_at descending
            history_records_result = await session.execute(
                select(history_class).where(
                    history_class.internal_record_id == internal_record_id
                ).order_by(history_class.approved_at.desc())
            )
            history_records = history_records_result.scalars().all()

            # Get base columns from G2PRegisterHistory model
            from ..models import G2PRegisterHistory
            base_columns = set(G2PRegisterHistory.__table__.columns.keys()) if hasattr(G2PRegisterHistory, '__table__') else set()
            # Also include the abstract class columns
            base_columns.update([
                'history_record_id', 'internal_record_id', 'change_request_id', 'tab_id', 'section_id',
                'is_primary_section', 'application_id', 'change_request_source', 'created_by', 'created_at',
                'approved_by', 'approved_at'
            ])

            # Get all columns from history_class to identify additional fields
            history_columns = set(history_class.__table__.columns.keys())
            additional_columns = history_columns - base_columns

            history_data_list: list[RecordHistoryData] = []
            for history_record in history_records:
                # Build base record data dict
                record_data_dict = {
                    'history_record_id': history_record.history_record_id,
                    'internal_record_id': history_record.internal_record_id,
                    'change_request_id': history_record.change_request_id,
                    'tab_id': history_record.tab_id,
                    'section_id': history_record.section_id,
                    'is_primary_section': history_record.is_primary_section,
                    'application_id': history_record.application_id,
                    'change_request_source': history_record.change_request_source.value if history_record.change_request_source else None,
                    'created_by': history_record.created_by,
                    'created_at': history_record.created_at.isoformat() if history_record.created_at else None,
                    'approved_by': history_record.approved_by,
                    'approved_at': history_record.approved_at.isoformat() if history_record.approved_at else None,
                }

                # Add additional domain-specific fields
                for col in additional_columns:
                    value = getattr(history_record, col, None)
                    # Handle datetime serialization
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    record_data_dict[col] = value

                history_data: RecordHistoryData = RecordHistoryData(**record_data_dict)
                history_data_list.append(history_data)

            return RecordHistoryListData(
                register_id=register_id,
                internal_record_id=internal_record_id,
                tab_id=tab_id,
                history_records=history_data_list
            )

    async def get_version_dates(self, register_id: str, internal_record_id: str, tab_id: str) -> VersionDatesData:
        """Get unique truncated dates from history records for a given register, internal_record_id and tab_id"""
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

            # Fetch all sections for the given tab_id
            sections_result = await session.execute(
                select(G2PRegisterSection).where(
                    G2PRegisterSection.register_id == register_id,
                    G2PRegisterSection.tab_id == tab_id
                )
            )
            sections = sections_result.scalars().all()

            # Collect unique section_register_ids
            unique_section_register_ids = set()
            for section in sections:
                unique_section_register_ids.add(section.section_register_id)

            # Collect unique dates from all history classes
            unique_dates = set()
            module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
            history_class_prefix = "G2PRegisterHistory"

            for section_register_id in unique_section_register_ids:
                # Get register definition for this section
                section_register_def = (
                    await session.execute(
                        select(G2PRegisterDefinition).where(
                            G2PRegisterDefinition.register_id == section_register_id
                        )
                    )
                ).scalar()
                
                if not section_register_def:
                    continue
                
                # Resolve history class for this section register
                history_class_name = f"{history_class_prefix}{section_register_def.register_mnemonic}"
                try:
                    history_class = getattr(module, history_class_name)
                except AttributeError:
                    continue
                
                # Query history records where internal_record_id OR link_internal_record_id matches
                history_records_result = await session.execute(
                    select(history_class).where(
                        history_class.tab_id == tab_id,
                        or_(
                            history_class.internal_record_id == internal_record_id,
                            history_class.link_internal_record_id == internal_record_id
                        )
                    )
                )
                history_records = history_records_result.scalars().all()
                
                # Extract dates from this history class
                for history_record in history_records:
                    if history_record.created_at:
                        truncated_date = history_record.created_at.date().isoformat()
                        unique_dates.add(truncated_date)

            # Sort dates in descending order (most recent first)
            sorted_dates = sorted(list(unique_dates), reverse=True)

            return VersionDatesData(
                register_id=register_id,
                internal_record_id=internal_record_id,
                tab_id=tab_id,
                version_dates=sorted_dates
            )

    async def get_versions_for_a_date(self, register_id: str, internal_record_id: str, tab_id: str, truncated_created_date: str) -> list[VersionsForDateData]:
        """Get changes from history records for a given register, internal_record_id, tab_id and specific date, grouped by section"""
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

            # Fetch all sections for the given tab_id
            sections_result = await session.execute(
                select(G2PRegisterSection).where(
                    G2PRegisterSection.register_id == register_id,
                    G2PRegisterSection.tab_id == tab_id
                )
            )
            sections = sections_result.scalars().all()

            module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
            history_class_prefix = "G2PRegisterHistory"

            results = []
            for section in sections:
                # Get register definition for this section
                section_register_def = (
                    await session.execute(
                        select(G2PRegisterDefinition).where(
                            G2PRegisterDefinition.register_id == section.section_register_id
                        )
                    )
                ).scalar()
                
                if not section_register_def:
                    continue
                
                # Resolve history class for this section register
                history_class_name = f"{history_class_prefix}{section_register_def.register_mnemonic}"
                try:
                    history_class = getattr(module, history_class_name)
                except AttributeError:
                    continue
                
                # Query history records where internal_record_id OR link_internal_record_id matches
                history_records_result = await session.execute(
                    select(history_class).where(
                        history_class.tab_id == tab_id,
                        or_(
                            history_class.internal_record_id == internal_record_id,
                            history_class.link_internal_record_id == internal_record_id
                        )
                    ).order_by(history_class.created_at.desc())
                )
                history_records = history_records_result.scalars().all()
                
                # Filter by truncated date and build changes list for this section
                section_changes = []
                for history_record in history_records:
                    if history_record.created_at:
                        record_date = history_record.created_at.date().isoformat()
                        if record_date == truncated_created_date:
                            section_changes.append(VersionForDateData(
                                change_request_id=history_record.change_request_id,
                                created_at=history_record.created_at.isoformat()
                            ))
                
                # Only add section if it has changes
                if section_changes:
                    results.append(VersionsForDateData(
                        register_id=register_id,
                        internal_record_id=internal_record_id,
                        tab_id=tab_id,
                        truncated_created_date=truncated_created_date,
                        section_id=section.section_id,
                        section_mnemonic=section.section_mnemonic,
                        changes=section_changes
                    ))

            return results

    async def get_number_of_pending_change_requests(self, subject_register_id: str, subject_record_id: str, tab_id: str) -> NumberOfPendingChangeRequestsData:
        """Get the number of pending change requests for a given register, internal_record_id and tab_id"""
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

            # Count pending change requests for the given internal_record_id and tab_id
            count_result = await session.execute(
                select(func.count()).select_from(G2PRegisterChangeRequest).where(
                    (G2PRegisterChangeRequest.register_id == subject_register_id) &
                    (G2PRegisterChangeRequest.internal_record_id == subject_record_id) &
                    (G2PRegisterChangeRequest.tab_id == tab_id) &
                    (G2PRegisterChangeRequest.approval_status == ApprovalStatusEnum.PENDING.value)
                )
            )
            number_of_pending_change_requests = count_result.scalar_one()

            return NumberOfPendingChangeRequestsData(
                subject_register_id=subject_register_id,
                subject_record_id=subject_record_id,
                tab_id=tab_id,
                number_of_pending_change_requests=number_of_pending_change_requests
            )

    async def get_number_of_cross_register_changes(self, subject_register_id: str, subject_record_id: str) -> NumberOfCrossRegisterChangesData:
        """Get the number of cross-register pending change requests by searching subject_record_id in search_text of G2PRegisterChangeRequestPayload"""
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

            # Count pending change requests where search_text contains subject_record_id
            # Join G2PRegisterChangeRequest with G2PRegisterChangeRequestPayload and search in search_text
            count_result = await session.execute(
                select(func.count()).select_from(G2PRegisterChangeRequest).join(
                    G2PRegisterChangeRequestPayload,
                    G2PRegisterChangeRequest.change_request_id == G2PRegisterChangeRequestPayload.change_request_id
                ).where(
                    (G2PRegisterChangeRequest.approval_status == ApprovalStatusEnum.PENDING.value) &
                    (G2PRegisterChangeRequestPayload.search_text.ilike(f"%{subject_record_id}%"))
                )
            )
            number_of_cross_register_changes = count_result.scalar_one()

            return NumberOfCrossRegisterChangesData(
                subject_register_id=subject_register_id,
                subject_record_id=subject_record_id,
                number_of_cross_register_changes=number_of_cross_register_changes
            )

    async def get_cross_register_changes(self, subject_register_id: str, subject_record_id: str) -> list[CrossRegisterChangeRequestData]:
        """Get the list of cross-register pending change requests by searching subject_record_id in search_text of G2PRegisterChangeRequestPayload"""
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

            # Fetch pending change requests where search_text contains subject_record_id
            # Join G2PRegisterChangeRequest with G2PRegisterChangeRequestPayload, G2PRegisterDefinition, and G2PRegisterUITab
            result = await session.execute(
                select(
                    G2PRegisterChangeRequest,
                    G2PRegisterDefinition.register_mnemonic,
                    G2PRegisterUITab.tab_label
                ).join(
                    G2PRegisterChangeRequestPayload,
                    G2PRegisterChangeRequest.change_request_id == G2PRegisterChangeRequestPayload.change_request_id
                ).join(
                    G2PRegisterDefinition,
                    G2PRegisterChangeRequest.register_id == G2PRegisterDefinition.register_id
                ).join(
                    G2PRegisterUITab,
                    G2PRegisterChangeRequest.tab_id == G2PRegisterUITab.tab_id
                ).where(
                    (G2PRegisterChangeRequest.approval_status == ApprovalStatusEnum.PENDING.value) &
                    (G2PRegisterChangeRequestPayload.search_text.ilike(f"%{subject_record_id}%"))
                ).order_by(G2PRegisterChangeRequest.created_at.desc())
            )
            rows = result.all()

            cross_register_changes: list[CrossRegisterChangeRequestData] = []
            for row in rows:
                change_request = row[0]
                register_mnemonic = row[1]
                tab_label = row[2]
                cross_register_changes.append(CrossRegisterChangeRequestData(
                    change_request_id=change_request.change_request_id,
                    register_id=change_request.register_id,
                    register_mnemonic=register_mnemonic,
                    tab_id=change_request.tab_id,
                    tab_label=tab_label,
                    internal_record_id=change_request.internal_record_id,
                    section_id=change_request.section_id,
                    source_partner_id=change_request.source_partner_id,
                    created_by=change_request.created_by,
                    created_at=change_request.created_at.isoformat() if change_request.created_at else None,
                    no_of_verifications_required=change_request.no_of_verifications_required,
                    no_of_verifications_done=change_request.no_of_verifications_done,
                    approval_status=change_request.approval_status,
                    approved_by=change_request.approved_by,
                    approved_at=change_request.approved_at.isoformat() if change_request.approved_at else None
                ))

            return cross_register_changes

    async def _fetch_change_requests(self, subject_register_id: str, subject_record_id: str, tab_id: str, current_page: int, page_size: int, sort_by: str, filter_by: dict, session) -> tuple[list[ChangeRequestData], int]:
        """Helper method to fetch all change requests for a specific internal record and tab with pagination"""
        # Build base query
        base_query = select(G2PRegisterChangeRequest, G2PRegisterChangeRequestPayload).join(
            G2PRegisterChangeRequestPayload,
            G2PRegisterChangeRequest.change_request_id == G2PRegisterChangeRequestPayload.change_request_id
        ).where(
            (G2PRegisterChangeRequest.register_id == subject_register_id) &
            (G2PRegisterChangeRequest.internal_record_id == subject_record_id) &
            (G2PRegisterChangeRequest.tab_id == tab_id)
        ).order_by(G2PRegisterChangeRequest.created_at.desc())

        # Get total count
        count_result = await session.execute(select(func.count()).select_from(G2PRegisterChangeRequest).where(
            (G2PRegisterChangeRequest.register_id == subject_register_id) &
            (G2PRegisterChangeRequest.internal_record_id == subject_record_id) &
            (G2PRegisterChangeRequest.tab_id == tab_id)
        ))
        total_items = count_result.scalar() or 0

        # Apply pagination
        offset = (current_page - 1) * page_size
        query = base_query.offset(offset).limit(page_size)

        result = await session.execute(query)
        change_requests = result.all()

        change_requests_list: list[ChangeRequestData] = []

        # Convert ORM objects to ChangeRequestData while still in session context
        for change_request, payload in change_requests:
            # Convert datetime objects to strings
            created_at_str = str(change_request.created_at.isoformat()) if change_request.created_at and hasattr(change_request.created_at, 'isoformat') else None
            approved_at_str = str(change_request.approved_at.isoformat()) if change_request.approved_at and hasattr(change_request.approved_at, 'isoformat') else None

            # Get change_payload from the payload object
            change_payload = payload.change_payload if payload else None

            # Create ChangeRequestData object
            # Note: current_register_data is not populated in list view for performance reasons
            change_request_data: ChangeRequestData = ChangeRequestData(
                change_request_id=change_request.change_request_id,
                register_id=change_request.register_id,
                tab_id=change_request.tab_id,
                internal_record_id=change_request.internal_record_id,
                section_id=change_request.section_id,
                section_mnemonic=change_request.section_mnemonic,
                source_partner_id=change_request.source_partner_id,
                created_by=change_request.created_by,
                created_at=created_at_str,
                no_of_verifications_required=change_request.no_of_verifications_required,
                no_of_verifications_done=change_request.no_of_verifications_done,
                approval_status=change_request.approval_status,
                approved_by=change_request.approved_by,
                approved_at=approved_at_str,
                change_payload=change_payload,
                current_register_data=None
            )
            change_requests_list.append(change_request_data)

        return change_requests_list, total_items

    async def _fetch_change_request(self, change_request_id: str, session) -> ChangeRequestData:
        """Helper method to fetch a single change request by ID"""
        # Join G2PRegisterChangeRequest with G2PRegisterChangeRequestPayload
        result = await session.execute(
            select(G2PRegisterChangeRequest, G2PRegisterChangeRequestPayload).join(
                G2PRegisterChangeRequestPayload,
                G2PRegisterChangeRequest.change_request_id == G2PRegisterChangeRequestPayload.change_request_id
            ).where(
                G2PRegisterChangeRequest.change_request_id == change_request_id
            )
        )
        change_request_row = result.first()

        if not change_request_row:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_FOUND.value[0]
            )

        change_request, change_request_payload = change_request_row

        # Convert datetime objects to strings
        created_at_str = str(change_request.created_at.isoformat()) if change_request.created_at and hasattr(change_request.created_at, 'isoformat') else None
        approved_at_str = str(change_request.approved_at.isoformat()) if change_request.approved_at and hasattr(change_request.approved_at, 'isoformat') else None

        # Get change_payload from the payload object
        change_payloads: list[ChangePayload] = change_request_payload.change_payload if change_request_payload else None

        # Fetch existing register data (old values) for current_register_data
        current_register_data = None
        current_register_data_list = []
        try:
            # Get the register definition to find the implementation class
            g2p_register_definition: G2PRegisterDefinition = (
                await session.execute(
                    select(G2PRegisterDefinition).where(
                        G2PRegisterDefinition.register_id == change_request.section_register_id
                    )
                )
            ).scalar()

            if g2p_register_definition:
                # Get the implementation class for this register
                try:
                    module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
                    register_class_prefix: str = "G2PRegister"
                    implementation_class_name: str = f"{register_class_prefix}{g2p_register_definition.register_mnemonic}"
                    implementation_class = getattr(module, implementation_class_name)

                    internal_record_ids = [change_payload.get("internal_record_id") for change_payload in change_payloads if change_payload.get("internal_record_id")]
                    # Fetch the existing record by internal_record_id
                    existing_records = (
                        await session.execute(
                            select(implementation_class).where(
                                implementation_class.internal_record_id.in_(internal_record_ids)
                            )
                        )
                    ).scalars().all()

                    for existing_record in existing_records:
                        if existing_record:
                            # Convert ORM object to dict for current_register_data
                            mapper = inspect(existing_record.__class__)
                            current_register_data = {}

                            # Base fields to exclude from current_register_data
                            base_fields: set = {'search_text'}

                            for column in mapper.columns:
                                column_name: str = column.name
                                if column_name not in base_fields:
                                    value = getattr(existing_record, column_name, None)

                                    # Convert datetime objects to strings
                                    if value is not None and hasattr(value, 'isoformat'):
                                        value = value.isoformat()

                                    current_register_data[column_name] = value
                            current_register_data_list.append(current_register_data)

                except (AttributeError, ModuleNotFoundError) as error:
                    _logger.warning(f"Could not fetch old register data for change request {change_request_id}: {str(error)}")
        except Exception as error:
            _logger.warning(f"Error fetching old register data for change request {change_request_id}: {str(error)}")

        g2p_register_section: G2PRegisterSection = (
            await session.execute(
                select(G2PRegisterSection).where(
                    G2PRegisterSection.section_id == change_request.section_id
                )
            )
        ).scalar()

        # Create ChangeRequestData object
        change_request_data: ChangeRequestData = ChangeRequestData(
            change_request_id=change_request.change_request_id,
            register_id=change_request.register_id,
            tab_id=change_request.tab_id,
            internal_record_id=change_request.internal_record_id,
            section_id=change_request.section_id,
            section_mnemonic=g2p_register_section.section_mnemonic,
            is_list=g2p_register_section.is_list,
            section_register_id=change_request.section_register_id,
            source_partner_id=change_request.source_partner_id,
            created_by=change_request.created_by,
            created_at=created_at_str,
            no_of_verifications_required=change_request.no_of_verifications_required,
            no_of_verifications_done=change_request.no_of_verifications_done,
            approval_status=change_request.approval_status,
            approved_by=change_request.approved_by,
            approved_at=approved_at_str,
            change_payload=change_payloads,
            current_register_data=current_register_data_list
        )

        return change_request_data

    async def _fetch_change_requests_flattened(self, subject_register_id: str, subject_record_id: str, tab_id: str, current_page: int, page_size: int, sort_by: str, filter_by: dict, session) -> tuple[list[ChangeRequestFlattenedData], int]:
        """Helper method to fetch all change requests with flattened change_payload fields"""
        # Build base query
        base_query = select(G2PRegisterChangeRequest, G2PRegisterChangeRequestPayload).join(
            G2PRegisterChangeRequestPayload,
            G2PRegisterChangeRequest.change_request_id == G2PRegisterChangeRequestPayload.change_request_id
        ).where(
            (G2PRegisterChangeRequest.register_id == subject_register_id) &
            (G2PRegisterChangeRequest.internal_record_id == subject_record_id) &
            (G2PRegisterChangeRequest.tab_id == tab_id)
        ).order_by(G2PRegisterChangeRequest.created_at.desc())

        # Get total count
        count_result = await session.execute(select(func.count()).select_from(G2PRegisterChangeRequest).where(
            (G2PRegisterChangeRequest.register_id == subject_register_id) &
            (G2PRegisterChangeRequest.internal_record_id == subject_record_id) &
            (G2PRegisterChangeRequest.tab_id == tab_id)
        ))
        total_items = count_result.scalar() or 0

        # Apply pagination
        offset = (current_page - 1) * page_size
        query = base_query.offset(offset).limit(page_size)

        result = await session.execute(query)
        change_requests = result.all()

        change_requests_list: list[ChangeRequestFlattenedData] = []

        # Convert ORM objects to ChangeRequestFlattenedData with flattened fields
        for change_request, payload in change_requests:
            # Convert datetime objects to strings
            created_at_str = str(change_request.created_at.isoformat()) if change_request.created_at and hasattr(change_request.created_at, 'isoformat') else None
            approved_at_str = str(change_request.approved_at.isoformat()) if change_request.approved_at and hasattr(change_request.approved_at, 'isoformat') else None

            # Get change_payload from the payload object
            change_payload = payload.change_payload if payload else {}

            # Get section to retrieve section_mnemonic
            g2p_register_section: G2PRegisterSection = (
                await session.execute(
                    select(G2PRegisterSection).where(
                        G2PRegisterSection.section_id == change_request.section_id
                    )
                )
            ).scalar()

            # Create base ChangeRequestFlattenedData object
            change_request_data_dict = {
                "change_request_id": change_request.change_request_id,
                "register_id": change_request.register_id,
                "tab_id": change_request.tab_id,
                "internal_record_id": change_request.internal_record_id,
                "section_id": change_request.section_id,
                "section_mnemonic": g2p_register_section.section_mnemonic,
                "source_partner_id": change_request.source_partner_id,
                "created_by": change_request.created_by,
                "created_at": created_at_str,
                "no_of_verifications_required": change_request.no_of_verifications_required,
                "no_of_verifications_done": change_request.no_of_verifications_done,
                "approval_status": change_request.approval_status,
                "approved_by": change_request.approved_by,
                "approved_at": approved_at_str,
            }

            # Flatten change_payload fields into the main object
            if change_payload and isinstance(change_payload, dict):
                # Exclude internal_record_id from flattening as it's already in the main object
                for key, value in change_payload.items():
                    if key != "internal_record_id":
                        change_request_data_dict[key] = value

            # Create ChangeRequestFlattenedData object with flattened fields
            change_request_data: ChangeRequestFlattenedData = ChangeRequestFlattenedData(**change_request_data_dict)
            change_requests_list.append(change_request_data)

        return change_requests_list, total_items

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
            extra_fields: dict = {}

            # Get MinIO client for generating presigned URLs
            from ..helpers import MinioClient
            minio_client: MinioClient = MinioClient.get_component()

            for column in mapper.columns:
                column_name: str = column.name
                value = getattr(record, column_name, None)

                # Convert datetime objects to strings
                if value is not None and hasattr(value, 'isoformat'):
                    value = value.isoformat()

                # Convert image field to record_image_url with presigned URL
                if column_name == 'image' and value:
                    extra_fields['record_image_url'] = minio_client.get_url(object_name=value)
                else:
                    # Add to extra_fields if not a base field
                    extra_fields[column_name] = value

            # Create RecordData object with flattened extra fields
            record_data: RecordData = RecordData(
                **extra_fields
            )

            return record_data

    async def get_verifications_for_change_request(self, change_request_id: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[VerificationData], int]:
        """Get all verifications for a specific change request with pagination"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate change request exists (without checking approval status)
            change_request: G2PRegisterChangeRequest = (
                await session.execute(
                    select(G2PRegisterChangeRequest).where(
                        G2PRegisterChangeRequest.change_request_id == change_request_id
                    )
                )
            ).scalar()
            if not change_request:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_FOUND.value[0]
                )

            # Get total count
            count_result = await session.execute(select(func.count()).select_from(G2PRegisterVerification).where(
                G2PRegisterVerification.change_request_id == change_request_id
            ))
            total_items = count_result.scalar() or 0

            # Apply pagination
            offset = (current_page - 1) * page_size
            verifications = (
                await session.execute(
                    select(G2PRegisterVerification).where(
                        G2PRegisterVerification.change_request_id == change_request_id
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
                    change_request_id=verification.change_request_id,
                    verified_by=verification.verified_by,
                    verified_at=verified_at_str,
                    verification_observations=verification.verification_observations,
                    is_approved=verification.is_approved
                )
                verifications_list.append(verification_data)

            return verifications_list, total_items

    async def add_verification_for_change_request(
        self,
        payload: AddVerificationPayload
    ) -> VerificationData:
        """
        Add a new verification for a change request.

        Args:
            payload: AddVerificationPayload containing change_request_id, verification_observations, is_approved

        Returns:
            VerificationData: The created verification

        Raises:
            G2PRegistryException: If change request not found or other validation errors
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate change request exists
            change_request_result = await session.execute(
                select(G2PRegisterChangeRequest).where(
                    G2PRegisterChangeRequest.change_request_id == payload.change_request_id
                )
            )
            change_request = change_request_result.scalar_one_or_none()

            if not change_request:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_FOUND.value[0]
                )

            # Create new verification
            verification_id = str(uuid.uuid4())
            verification = G2PRegisterVerification(
                verification_id=verification_id,
                register_id=change_request.register_id,
                internal_record_id=change_request.internal_record_id,
                section_id=change_request.section_id,
                change_request_id=payload.change_request_id,
                verified_by="system",  # Will be set by controller with actual user
                verified_at=datetime.now(),
                verification_observations=payload.verification_observations,
                is_approved=payload.is_approved
            )
            session.add(verification)
            change_request.no_of_verifications_done += 1
            session.add(change_request)
            await session.commit()
            await session.refresh(verification)

            # Return verification data
            verification_data = VerificationData(
                verification_id=verification.verification_id,
                register_id=verification.register_id,
                internal_record_id=verification.internal_record_id,
                section_id=verification.section_id,
                change_request_id=verification.change_request_id,
                verified_by=verification.verified_by,
                verified_at=verification.verified_at.isoformat() if verification.verified_at else None,
                verification_observations=verification.verification_observations,
                is_approved=verification.is_approved
            )

            return verification_data

    async def get_deduplication_register_results(self, change_request_id: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[DeduplicationRegisterResultData], int]:
        """
        Get deduplication results for a change request against register records with pagination.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Get total count
            count_result = await session.execute(select(func.count()).select_from(DeduplicationRegisterResult).where(
                DeduplicationRegisterResult.change_request_id == change_request_id
            ))
            total_items = count_result.scalar() or 0

            # Apply pagination
            offset = (current_page - 1) * page_size
            results = (
                await session.execute(
                    select(DeduplicationRegisterResult).where(
                        DeduplicationRegisterResult.change_request_id == change_request_id
                    ).offset(offset).limit(page_size)
                )
            ).scalars().all()

            # Convert to schema objects
            dedup_result_data_list = []
            for result in results:
                dedup_result_data = DeduplicationRegisterResultData(
                    dedup_result_id=result.dedup_result_id,
                    change_request_id=result.change_request_id,
                    internal_record_id=result.internal_record_id,
                    match_score=result.match_score,
                    field_matches=result.field_matches,
                    created_at=result.created_at.isoformat() if result.created_at else None
                )
                dedup_result_data_list.append(dedup_result_data)

            return dedup_result_data_list, total_items

    async def get_deduplication_change_request_results(self, change_request_id: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[DeduplicationChangerequestResultData], int]:
        """
        Get deduplication results for a change request against other change requests with pagination.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Get total count
            count_result = await session.execute(select(func.count()).select_from(DeduplicationChangerequestResult).where(
                DeduplicationChangerequestResult.change_request_id == change_request_id
            ))
            total_items = count_result.scalar() or 0

            # Apply pagination
            offset = (current_page - 1) * page_size
            results = (
                await session.execute(
                    select(DeduplicationChangerequestResult).where(
                        DeduplicationChangerequestResult.change_request_id == change_request_id
                    ).offset(offset).limit(page_size)
                )
            ).scalars().all()

            # Convert to schema objects
            dedup_result_data_list = []
            for result in results:
                dedup_result_data = DeduplicationChangerequestResultData(
                    dedup_result_id=result.dedup_result_id,
                    change_request_id=result.change_request_id,
                    candidate_change_request_id=result.candidate_change_request_id,
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

    async def get_register_tab_sections(self, register_id: str, tab_id: str) -> list[RegisterSectionData]:
        """
        Get register sections for a given register_id and tab_id.
        Returns a list of section UI schema configurations from g2p_register_sections table
        filtered by both register_id and tab_id.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            await self.validate_register_definition(register_id, session)

            # Fetch register sections filtered by tab_id
            register_tab_sections_list: list[RegisterSectionData] = await self._fetch_register_tab_sections(register_id, tab_id, session)
            return register_tab_sections_list

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

    async def _fetch_register_tab_sections(self, register_id: str, tab_id: str, session) -> list[RegisterSectionData]:
        """Fetch register sections from g2p_register_sections table filtered by tab_id."""
        result = await session.execute(
            select(G2PRegisterSection).where(
                G2PRegisterSection.register_id == register_id,
                G2PRegisterSection.tab_id == tab_id
            )
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
                section_order=section.section_order,
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

    async def update_dedup_is_enabled(
        self,
        register_id: str,
        dedup_is_enabled: bool
    ) -> RegisterSchemaData:
        """
        Update the dedup_is_enabled flag for a register.
        This is stored in the register definition, not the schema.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate and get register definition
            result = await session.execute(
                select(G2PRegisterDefinition).where(G2PRegisterDefinition.register_id == register_id)
            )
            register_definition = result.scalar()

            if not register_definition:
                raise ValueError(f"Register definition does not exist for register_id: {register_id}")

            register_definition.dedup_is_enabled = dedup_is_enabled
            await session.commit()

            _logger.info(f"Updated dedup_is_enabled to {dedup_is_enabled} for register_id: {register_id}")

            # Return the schema data (fetch from schema table)
            return await self.get_register_schema(register_id)

    async def update_dedup_threshold_score(
        self,
        register_id: str,
        dedup_threshold_score: float
    ) -> RegisterSchemaData:
        """
        Update the dedup_threshold_score for a register.
        This is stored in the register definition, not the schema.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate and get register definition
            result = await session.execute(
                select(G2PRegisterDefinition).where(G2PRegisterDefinition.register_id == register_id)
            )
            register_definition = result.scalar()

            if not register_definition:
                raise ValueError(f"Register definition does not exist for register_id: {register_id}")

            register_definition.dedup_threshold_score = dedup_threshold_score
            await session.commit()

            _logger.info(f"Updated dedup_threshold_score to {dedup_threshold_score} for register_id: {register_id}")

            # Return the schema data (fetch from schema table)
            return await self.get_register_schema(register_id)

    async def update_deduplication_schema(
        self,
        register_id: str,
        deduplicate_schema: list[dict]
    ) -> RegisterSchemaData:
        """
        Update the deduplicate_schema for a register.
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
                raise ValueError(f"Register schema does not exist for register_id: {register_id}.")

            existing_schema.deduplicate_schema = deduplicate_schema
            await session.commit()

            _logger.info(f"Updated deduplicate_schema for register_id: {register_id}")

            return RegisterSchemaData(
                register_id=register_id,
                deduplicate_schema=existing_schema.deduplicate_schema,
                search_result_schema=existing_schema.search_result_schema,
                filter_schema=existing_schema.filter_schema
            )

    async def update_search_result_schema(
        self,
        register_id: str,
        search_result_schema: list[dict]
    ) -> RegisterSchemaData:
        """
        Update the search_result_schema for a register.
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
                raise ValueError(f"Register schema does not exist for register_id: {register_id}.")

            existing_schema.search_result_schema = search_result_schema
            await session.commit()

            _logger.info(f"Updated search_result_schema for register_id: {register_id}")

            return RegisterSchemaData(
                register_id=register_id,
                deduplicate_schema=existing_schema.deduplicate_schema,
                search_result_schema=existing_schema.search_result_schema,
                filter_schema=existing_schema.filter_schema
            )
    
    async def get_primary_register_section(self, register_id: str) -> RegisterSectionData | None:
        """
        Get the primary section for a register.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(G2PRegisterSection).where(
                    (G2PRegisterSection.register_id == register_id) &
                    (G2PRegisterSection.is_primary_section == True)
                )
            )
            primary_section: G2PRegisterSection = result.scalar()

            if not primary_section:
                return None

            return RegisterSectionData(
                section_register_id=primary_section.section_register_id,
                register_id=primary_section.register_id,
                tab_id=primary_section.tab_id,
                section_id=primary_section.section_id,
                section_mnemonic=primary_section.section_mnemonic,
                section_description=primary_section.section_description,
                documents_required=primary_section.documents_required,
                no_of_verifications_required=primary_section.no_of_verifications_required,
                auto_approval=primary_section.auto_approval,
                is_list=primary_section.is_list,
                is_primary_section=primary_section.is_primary_section,
                section_ui_schema=primary_section.section_ui_schema
            )

    # =========================================================================
    # Document Upload and Handling Methods
    # =========================================================================

    async def upload_documents(
        self,
        document_label: str,
        documents: list,  # List of documents
    ) -> UploadDocumentsResponseData:
        """
        Upload documents to MinIO and return document store IDs with label.

        Args:
            document_label: The label for the documents being uploaded
            documents: List of UploadFile objects (documents) to upload

        Returns:
            UploadDocumentsResponseData with list of uploaded document info
        """
        from ..helpers import MinioClient

        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
           
            minio_client: MinioClient = MinioClient.get_component()
            uploaded_documents: list[UploadedDocumentData] = []

            for document in documents:
                
                # Read file content
                document_content = await document.read()

                # Generate unique object name
                object_name = f"{document_label.lower()}/{uuid.uuid4().hex}_{document.filename}"

                # Upload to MinIO
                import io
                document_store_id = minio_client.put_object(
                    object_name=object_name,
                    data=io.BytesIO(document_content),
                    length=len(document_content),
                    content_type=document.content_type or "application/octet-stream",
                )

                # Generate presigned URL for the uploaded document
                document_url = minio_client.get_url(object_name=document_store_id)

                # Persist document metadata (without URL, which is regenerated when needed)
                session.add(G2PRegistryDocument(
                    document_store_id=document_store_id,
                    document_label=document_label,
                    filename=document.filename,
                ))

                uploaded_documents.append(UploadedDocumentData(
                    document_store_id=document_store_id,
                    document_label=document_label,
                    filename=document.filename,
                    document_url=document_url
                ))

            await session.commit()

            return UploadDocumentsResponseData(uploaded_documents=uploaded_documents)

    async def _handle_documents_on_approval(
        self,
        change_request: G2PRegisterChangeRequest,
        section: G2PRegisterSection,
        session
    ) -> None:
        """
        Handle documents when a change request is approved.
        - Move documents from change request to section documents (replace existing with same label)
        - Create document history entries
        """
        # Fetch documents attached to this change request
        docs_result = await session.execute(
            select(G2PRegisterChangeRequestDocument).where(
                G2PRegisterChangeRequestDocument.change_request_id == change_request.change_request_id
            )
        )
        change_request_documents = docs_result.scalars().all()

        if not change_request_documents:
            _logger.info(f"No documents to process for change request {change_request.change_request_id}")
            return

        for cr_doc in change_request_documents:
             # Create history entry for the old document before replacing
            history_entry = G2PRegisterDocumentHistory(
                internal_record_id=change_request.internal_record_id,
                change_request_id=change_request.change_request_id,
                section_id=section.section_id,
                document_label=cr_doc.document_label,
                document_store_id=cr_doc.document_store_id,
                created_by=change_request.created_by,
                created_at=change_request.created_at,
                approved_by="system",
                approved_at=datetime.now()
            )
            session.add(history_entry)
            # Check if a document with the same label already exists for this section/record
            existing_doc_result = await session.execute(
                select(G2PRegisterSectionDocument).where(
                    (G2PRegisterSectionDocument.internal_record_id == change_request.internal_record_id) &
                    (G2PRegisterSectionDocument.section_id == section.section_id) &
                    (G2PRegisterSectionDocument.document_label == cr_doc.document_label)
                )
            )
            existing_doc = existing_doc_result.scalar()

            if existing_doc:
                # Update existing document with new store ID
                existing_doc.document_store_id = cr_doc.document_store_id
                _logger.info(f"Replaced document {cr_doc.document_label} for record {change_request.internal_record_id}")
            else:
                # Create new section document
                new_section_doc = G2PRegisterSectionDocument(
                    internal_record_id=change_request.internal_record_id,
                    register_id=section.register_id,
                    section_id=section.section_id,
                    document_label=cr_doc.document_label,
                    document_store_id=cr_doc.document_store_id
                )
                session.add(new_section_doc)
                _logger.info(f"Created new document {cr_doc.document_label} for record {change_request.internal_record_id}")

    async def get_section_documents(
        self,
        register_id: str,
        record_id: str,
        section_id: str
    ) -> SectionDocumentsData:
        """
        Get documents for a section record.

        Args:
            register_id: The register ID
            record_id: The internal record ID
            section_id: The section ID

        Returns:
            SectionDocumentsData with list of documents (label, document_store_id, document_url)
        """

        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate section exists
            await self.validate_section(section_id, session)

            # Get all documents for this record/section
            docs_result = await session.execute(
                select(G2PRegisterSectionDocument).where(
                    (G2PRegisterSectionDocument.register_id == register_id) &
                    (G2PRegisterSectionDocument.internal_record_id == record_id) &
                    (G2PRegisterSectionDocument.section_id == section_id)
                )
            )
            g2p_register_section_documents = docs_result.scalars().all()

            minio_client: MinioClient = MinioClient.get_component()

            # Get document labels for each document
            documents = []
            for g2p_register_section_document in g2p_register_section_documents:    

                # Generate presigned URL for the document
                document_url = minio_client.get_url(object_name=g2p_register_section_document.document_store_id)

                documents.append(
                    SectionDocumentData(
                        document_label=g2p_register_section_document.document_label,
                        document_store_id=g2p_register_section_document.document_store_id,
                        document_url=document_url
                    )
                )

            return SectionDocumentsData(
                register_id=register_id,
                record_id=record_id,
                section_id=section_id,
                documents=documents
            )

    async def get_change_request_documents(
        self,
        change_request_id: str
    ) -> ChangeRequestDocumentsData:
        """
        Get documents for a change request.

        Args:
            change_request_id: The change request ID

        Returns:
            ChangeRequestDocumentsData with list of documents (label, document_store_id, document_url)
        """

        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate change request exists
            cr_result = await session.execute(
                select(G2PRegisterChangeRequest).where(
                    G2PRegisterChangeRequest.change_request_id == change_request_id
                )
            )
            change_request = cr_result.scalar()
            if not change_request:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.CHANGE_REQUEST_NOT_FOUND.value[0]
                )

            # Get all documents for this change request
            docs_result = await session.execute(
                select(G2PRegisterChangeRequestDocument).where(
                    G2PRegisterChangeRequestDocument.change_request_id == change_request_id
                )
            )
            g2p_register_change_request_documents = docs_result.scalars().all()

            minio_client: MinioClient = MinioClient.get_component()

            # Get document labels for each document
            documents = []
            for g2p_register_change_request_document in g2p_register_change_request_documents:

                # Generate presigned URL for the document
                document_url = minio_client.get_url(object_name=g2p_register_change_request_document.document_store_id)

                documents.append(
                    SectionDocumentData(
                        document_label=g2p_register_change_request_document.document_label,
                        document_store_id=g2p_register_change_request_document.document_store_id,
                        document_url=document_url
                    )
                )

            return ChangeRequestDocumentsData(
                change_request_id=change_request_id,
                documents=documents
            )

    # =============================================================================
    # Registry Configuration Methods
    # =============================================================================

    async def create_registry_configuration(
        self,
        registry_name: str,
        registry_logo: str = None
    ) -> RegistryConfigurationData:
        """Create a new registry configuration"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Check if configuration already exists
            stmt = select(G2PRegistryConfiguration)
            result = await session.execute(stmt)
            existing_config = result.scalar_one_or_none()

            if existing_config:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_CONFIGURATION_EXISTS.value,
                    message="Registry configuration already exists. Use update instead."
                )

            configuration_id = str(uuid.uuid4())
            registry_configuration = G2PRegistryConfiguration(
                configuration_id=configuration_id,
                registry_name=registry_name,
                registry_logo=registry_logo
            )
            session.add(registry_configuration)
            await session.commit()

            return RegistryConfigurationData(
                configuration_id=configuration_id,
                registry_name=registry_name,
                registry_logo=registry_logo
            )

    async def get_registry_configuration(self) -> RegistryConfigurationData:
        """Get the registry configuration"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            stmt = select(G2PRegistryConfiguration)
            result = await session.execute(stmt)
            registry_configuration = result.scalar_one_or_none()

            if not registry_configuration:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_CONFIGURATION_NOT_FOUND.value,
                    message="Registry configuration not found"
                )

            return RegistryConfigurationData(
                configuration_id=registry_configuration.configuration_id,
                registry_name=registry_configuration.registry_name,
                registry_logo=registry_configuration.registry_logo
            )

    async def update_registry_configuration(
        self,
        configuration_id: str,
        registry_name: str = None,
        registry_logo: str = None
    ) -> RegistryConfigurationData:
        """Update the registry configuration"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            stmt = select(G2PRegistryConfiguration).where(
                G2PRegistryConfiguration.configuration_id == configuration_id
            )
            result = await session.execute(stmt)
            registry_configuration = result.scalar_one_or_none()

            if not registry_configuration:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_CONFIGURATION_NOT_FOUND.value,
                    message="Registry configuration not found"
                )

            if registry_name is not None:
                registry_configuration.registry_name = registry_name
            if registry_logo is not None:
                registry_configuration.registry_logo = registry_logo

            await session.commit()

            return RegistryConfigurationData(
                configuration_id=registry_configuration.configuration_id,
                registry_name=registry_configuration.registry_name,
                registry_logo=registry_configuration.registry_logo
            )

    async def get_total_pending_change_requests(self) -> int:
        """Get the total number of pending change requests across all registers"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            stmt = select(func.count()).select_from(G2PRegisterChangeRequest).where(
                G2PRegisterChangeRequest.approval_status == ApprovalStatusEnum.PENDING.value
            )
            result = await session.execute(stmt)
            count = result.scalar()
            return count or 0

    async def get_earliest_pending_change_request(self) -> EarliestPendingChangeRequestData:
        """Get the earliest pending change request based on created_at"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            stmt = select(G2PRegisterChangeRequest).where(
                G2PRegisterChangeRequest.approval_status == ApprovalStatusEnum.PENDING.value
            ).order_by(G2PRegisterChangeRequest.created_at.asc()).limit(1)

            result = await session.execute(stmt)
            change_request = result.scalar_one_or_none()

            if not change_request:
                # Return empty data if no pending change requests
                return EarliestPendingChangeRequestData()

            # Get the change payload
            payload_stmt = select(G2PRegisterChangeRequestPayload).where(
                G2PRegisterChangeRequestPayload.change_request_id == change_request.change_request_id
            )
            payload_result = await session.execute(payload_stmt)
            payload = payload_result.scalar_one_or_none()

            return EarliestPendingChangeRequestData(
                change_request_id=change_request.change_request_id,
                register_id=change_request.register_id,
                tab_id=change_request.tab_id,
                internal_record_id=change_request.internal_record_id,
                section_id=change_request.section_id,
                source_partner_id=change_request.source_partner_id,
                created_by=change_request.created_by,
                created_at=str(change_request.created_at) if change_request.created_at else None,
                no_of_verifications_required=change_request.no_of_verifications_required,
                no_of_verifications_done=change_request.no_of_verifications_done,
                approval_status=change_request.approval_status,
                change_payload=payload.change_payload if payload else None
            )
