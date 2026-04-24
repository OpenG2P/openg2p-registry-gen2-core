import logging
import json
import uuid
import importlib
from datetime import datetime, date
from fastapi_cache.decorator import cache

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from openg2p_registry_core.schemas import ChangeRequestRequestPayload

from sqlalchemy.orm import Session
from sqlalchemy import func, insert, select, inspect, Date as SQLDate, or_, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from .g2p_register_hierarchical_service import G2PRegisterHierarchicalService

from ..helpers import MinioClient

from ..cache import metadata_key_builder

from ..models import (
    G2PRegisterChangeRequest, G2PRegisterChangeRequestPayload, G2PRegisterChangeRequestDocument,
    G2PRegisterDefinition, G2PRegisterSection, G2PRegisterVerification, ApprovalStatusEnum,
    DeduplicationRegisterResult, DeduplicationChangerequestResult, G2PRegisterSchema,
    G2PRegisterSection, G2PRegisterUITab, RegisterPurposeEnum, ChangeRequestSourceEnum,
    G2PRegisterSectionDocument, G2PRegisterDocumentHistory,
    G2PRegistryConfiguration, G2PRegistryTheme, G2PRegistryThemeValue, RegistryThemeAttributeNameEnum,
    G2PRegistryLanguage,
    G2PRegistryDocument, G2PFunctionalIdGenerationQueue, RecordStatusEnum
)
from ..schemas import (
    ChangeRequestRequestPayload, RegisterSummaryData, ChangeRequestSummaryData, RegisterData, AllRegistersRegisterData, ChildRegisterData,
    RegisterUITabData, SearchResultData, ChangeRequestSearchResultData, NumberOfVersionsData,
    RecordHistoryData, RecordHistoryListData, VersionDatesData, VersionForDateData, VersionsForDateData,
    NumberOfPendingChangeRequestsData, NumberOfCrossRegisterChangesData,
    CrossRegisterChangeRequestData, CrossRegisterChangesData, DeepSearchResultData,
    ChangeRequestData, ChangeRequestsData, ChangeRequestFlattenedData, RecordData,
    VerificationData, VerificationsData, AddVerificationPayload,
    DeduplicationRegisterResultsData, DeduplicationChangerequestResultsData,
    DeduplicationRegisterResultData, DeduplicationChangerequestResultData,
    RegisterSchemaData, RegisterSectionData, RegisterSectionUISchemaData, DisplayField,
    UploadedDocumentData, UploadDocumentsResponseData,
    RegistryConfigurationData, RegistryThemeData, RegistryThemeValueData, ThemeAttributeValueInput, ThemeOperationData,
    RegistryLanguageData, LanguageOperationData,
    EarliestPendingChangeRequestData,
    ChangePayload, EditActionEnum, ChangeRequestDocumentsData, SectionDocumentData, SectionDocumentsData,
    RegisterRelationEnum
)
from .g2p_register_domain_service import G2PRegisterDomainService
from .g2p_score_compute_service import G2PScoreComputeService
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

    async def create_change_request(
        self,
        change_request_request_payload: ChangeRequestRequestPayload,
        source_partner_id: str = None,
        submission_id: str = None,
        created_by: str | None = None,
    ):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:

            g2p_register_definition: G2PRegisterDefinition = await self.validate_register_definition(change_request_request_payload.register_id, session)
            g2p_register_section: G2PRegisterSection = await self.validate_section(change_request_request_payload.section_id, session)

            # Extract internal_record_id from change_payload if present
            # Note: For new record creation, internal_record_id may be a new UUID that doesn't exist yet
            # We don't validate internal_record_id existence here - it will be created when the change request is approved

            g2p_register_change_request: G2PRegisterChangeRequest = await self.construct_change_request(
                change_request_request_payload,
                g2p_register_section,
                g2p_register_definition.register_mnemonic,
                source_partner_id,
                submission_id,
                created_by,
            )

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

    async def get_all_registers(self, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[AllRegistersRegisterData], int]:
        """Get all registers with pagination, master_register_mnemonic, and has_data fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            all_registers_list, total_items = await self._fetch_all_registers(session, current_page, page_size, sort_by, filter_by)
            return all_registers_list, total_items

    async def get_dashboard_registers(self) -> list[RegisterData]:
        """Get all registers for dashboard display (clone of get_all_registers)"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            dashboard_registers_list: list[RegisterData] = await self._fetch_dashboard_registers(session)
            return dashboard_registers_list

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

    async def get_register_tabs(
        self,
        register_id: str,
        current_page: int = 1,
        page_size: int = 10,
        used_for_new_intake_form: bool | None = None,
    ) -> tuple[list[RegisterUITabData], int]:
        """
        Get register tabs with pagination.
        Returns (tabs_list, total_count).
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self.validate_register_definition(register_id, session)
            register_tabs_list, total_count = await self._fetch_register_tabs_paginated(
                register_id,
                current_page,
                page_size,
                session,
                used_for_new_intake_form,
            )
            return register_tabs_list, total_count

    async def add_register_tab(
        self,
        register_id: str,
        tab_label: str,
        tab_order: int = 0,
        used_for_new_intake_form: bool = False,
        no_of_verifications_required: int = 0,
        intake_form_name: str | None = None,
        intake_form_description: str | None = None,
        intake_form_auto_approve: bool = False,
        is_active: bool = True
    ) -> RegisterUITabData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self.validate_register_definition(register_id, session)
            register_tab_data: RegisterUITabData = await self._create_register_tab(
                register_id,
                tab_label,
                tab_order,
                used_for_new_intake_form,
                no_of_verifications_required,
                intake_form_name,
                intake_form_description,
                intake_form_auto_approve,
                is_active,
                session,
            )
            return register_tab_data

    async def _create_register_tab(
        self,
        register_id: str,
        tab_label: str,
        tab_order: int,
        used_for_new_intake_form: bool,
        no_of_verifications_required: int,
        intake_form_name: str | None,
        intake_form_description: str | None,
        intake_form_auto_approve: bool,
        is_active: bool,
        session
    ) -> RegisterUITabData:
        new_tab: G2PRegisterUITab = G2PRegisterUITab(
            register_id=register_id,
            tab_label=tab_label,
            tab_order=tab_order,
            used_for_new_intake_form=used_for_new_intake_form,
            no_of_verifications_required=no_of_verifications_required,
            intake_form_name=intake_form_name,
            intake_form_description=intake_form_description,
            intake_form_auto_approve=intake_form_auto_approve,
            is_active=is_active,
        )
        session.add(new_tab)
        await session.commit()
        await session.refresh(new_tab)

        tab_data: RegisterUITabData = RegisterUITabData(
            tab_id=new_tab.tab_id,
            register_id=new_tab.register_id,
            tab_label=new_tab.tab_label,
            tab_order=new_tab.tab_order,
            used_for_new_intake_form=new_tab.used_for_new_intake_form,
            no_of_verifications_required=new_tab.no_of_verifications_required,
            intake_form_name=new_tab.intake_form_name,
            intake_form_description=new_tab.intake_form_description,
            intake_form_auto_approve=new_tab.intake_form_auto_approve,
            is_active=new_tab.is_active,
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
            tab_order=tab.tab_order,
            used_for_new_intake_form=tab.used_for_new_intake_form,
            no_of_verifications_required=tab.no_of_verifications_required,
            intake_form_name=tab.intake_form_name,
            intake_form_description=tab.intake_form_description,
            intake_form_auto_approve=tab.intake_form_auto_approve,
            is_active=tab.is_active,
        )

        await session.delete(tab)
        await session.commit()

        return tab_data

    async def edit_register_tab(
        self,
        tab_id: str,
        tab_label: str | None = None,
        tab_order: int | None = None,
        used_for_new_intake_form: bool | None = None,
        no_of_verifications_required: int | None = None,
        intake_form_name: str | None = None,
        intake_form_description: str | None = None,
        intake_form_auto_approve: bool | None = None,
        is_active: bool | None = None
    ) -> RegisterUITabData:
        """
        Edit an existing UI tab.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            tab: G2PRegisterUITab | None = await session.get(G2PRegisterUITab, tab_id)
            if not tab:
                raise ValueError(f"Tab with tab_id '{tab_id}' not found.")

            if tab_label is not None:
                tab.tab_label = tab_label

            if tab_order is not None:
                tab.tab_order = tab_order

            if used_for_new_intake_form is not None:
                tab.used_for_new_intake_form = used_for_new_intake_form

            if no_of_verifications_required is not None:
                tab.no_of_verifications_required = no_of_verifications_required

            if intake_form_name is not None:
                tab.intake_form_name = intake_form_name

            if intake_form_description is not None:
                tab.intake_form_description = intake_form_description

            if intake_form_auto_approve is not None:
                tab.intake_form_auto_approve = intake_form_auto_approve

            if is_active is not None:
                tab.is_active = is_active

            await session.commit()
            await session.refresh(tab)

            return RegisterUITabData(
                tab_id=tab.tab_id,
                register_id=tab.register_id,
                tab_label=tab.tab_label,
                tab_order=tab.tab_order,
                used_for_new_intake_form=tab.used_for_new_intake_form,
                no_of_verifications_required=tab.no_of_verifications_required,
                intake_form_name=tab.intake_form_name,
                intake_form_description=tab.intake_form_description,
                intake_form_auto_approve=tab.intake_form_auto_approve,
                is_active=tab.is_active,
            )

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
        cr_auto_approve_for_bene_portal: bool = False,
        cr_auto_approve_for_agent_portal: bool = False,
        cr_auto_approve_for_staff_portal: bool = False,
        cr_auto_approve_for_partner: bool = False,
        cr_auto_approve_for_intake_form: bool = False,
        is_list: bool = False,
        is_primary_section: bool = False,
        is_core_section: bool = False,
        section_ui_schema: dict = None
    ) -> RegisterSectionData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self.validate_register_definition(register_id, session)
            await self._validate_register_tab(register_id, tab_id, session)
            section_data: RegisterSectionData = await self._create_register_section(
                section_register_id, register_id, tab_id, section_mnemonic, section_description,
                documents_required, no_of_verifications_required, auto_approval,
                cr_auto_approve_for_bene_portal, cr_auto_approve_for_agent_portal,
                cr_auto_approve_for_staff_portal, cr_auto_approve_for_partner, cr_auto_approve_for_intake_form,
                is_list, is_primary_section, is_core_section, section_ui_schema, session
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
        cr_auto_approve_for_bene_portal: bool,
        cr_auto_approve_for_agent_portal: bool,
        cr_auto_approve_for_staff_portal: bool,
        cr_auto_approve_for_partner: bool,
        cr_auto_approve_for_intake_form: bool,
        is_list: bool,
        is_primary_section: bool,
        is_core_section: bool,
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
            cr_auto_approve_for_bene_portal=cr_auto_approve_for_bene_portal,
            cr_auto_approve_for_agent_portal=cr_auto_approve_for_agent_portal,
            cr_auto_approve_for_staff_portal=cr_auto_approve_for_staff_portal,
            cr_auto_approve_for_partner=cr_auto_approve_for_partner,
            cr_auto_approve_for_intake_form=cr_auto_approve_for_intake_form,
            is_list=is_list,
            is_primary_section=is_primary_section,
            is_core_section=is_core_section,
            section_ui_schema=section_ui_schema
        )
        session.add(new_section)
        await session.commit()
        await session.refresh(new_section)

        section_data: RegisterSectionData = await self._build_register_section_data(new_section, session)
        return section_data

    async def delete_register_section(self, section_id: str) -> RegisterSectionData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            section_data: RegisterSectionData = await self._delete_register_section(section_id, session)
            return section_data

    async def _delete_register_section(self, section_id: str, session) -> RegisterSectionData:
        section: G2PRegisterSection | None = await session.get(G2PRegisterSection, section_id)
        if not section:
            raise ValueError(f"Section with section_id '{section_id}' not found.")

        section_data: RegisterSectionData = await self._build_register_section_data(section, session)

        await session.delete(section)
        await session.commit()

        return section_data

    async def update_register_section(
        self,
        section_id: str,
        section_mnemonic: str = None,
        section_description: str = None,
        no_of_verifications_required: int = None,
        documents_required: bool = None,
        auto_approval: bool = None,
        cr_auto_approve_for_bene_portal: bool = None,
        cr_auto_approve_for_agent_portal: bool = None,
        cr_auto_approve_for_staff_portal: bool = None,
        cr_auto_approve_for_partner: bool = None,
        cr_auto_approve_for_intake_form: bool = None,
        is_primary_section: bool = None,
        is_core_section: bool = None
    ) -> RegisterSectionData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            section_data: RegisterSectionData = await self._update_register_section(
                section_id, section_mnemonic, section_description,
                no_of_verifications_required, documents_required, auto_approval,
                cr_auto_approve_for_bene_portal, cr_auto_approve_for_agent_portal,
                cr_auto_approve_for_staff_portal, cr_auto_approve_for_partner, cr_auto_approve_for_intake_form,
                is_primary_section, is_core_section, session
            )
            return section_data

    async def _update_register_section(
        self,
        section_id: str,
        section_mnemonic: str,
        section_description: str,
        no_of_verifications_required: int,
        documents_required: bool,
        auto_approval: bool,
        cr_auto_approve_for_bene_portal: bool,
        cr_auto_approve_for_agent_portal: bool,
        cr_auto_approve_for_staff_portal: bool,
        cr_auto_approve_for_partner: bool,
        cr_auto_approve_for_intake_form: bool,
        is_primary_section: bool,
        is_core_section: bool,
        session
    ) -> RegisterSectionData:
        section: G2PRegisterSection | None = await session.get(G2PRegisterSection, section_id)
        if not section:
            raise ValueError(f"Section with section_id '{section_id}' not found.")

        if section_mnemonic is not None:
            section.section_mnemonic = section_mnemonic
        if section_description is not None:
            section.section_description = section_description
        if no_of_verifications_required is not None:
            section.no_of_verifications_required = no_of_verifications_required
        if documents_required is not None:
            section.documents_required = documents_required
        if auto_approval is not None:
            section.auto_approval = auto_approval
        if cr_auto_approve_for_bene_portal is not None:
            section.cr_auto_approve_for_bene_portal = cr_auto_approve_for_bene_portal
        if cr_auto_approve_for_agent_portal is not None:
            section.cr_auto_approve_for_agent_portal = cr_auto_approve_for_agent_portal
        if cr_auto_approve_for_staff_portal is not None:
            section.cr_auto_approve_for_staff_portal = cr_auto_approve_for_staff_portal
        if cr_auto_approve_for_partner is not None:
            section.cr_auto_approve_for_partner = cr_auto_approve_for_partner
        if cr_auto_approve_for_intake_form is not None:
            section.cr_auto_approve_for_intake_form = cr_auto_approve_for_intake_form
        if is_core_section is not None:
            section.is_core_section = is_core_section
        if is_primary_section is not None:
            # If setting to primary, unset any other primary section under the same tab_id
            if is_primary_section:
                existing_primary_result = await session.execute(
                    select(G2PRegisterSection).where(
                        G2PRegisterSection.tab_id == section.tab_id,
                        G2PRegisterSection.is_primary_section.is_(True),
                        G2PRegisterSection.section_id != section_id
                    )
                )
                existing_primary_sections = existing_primary_result.scalars().all()
                for existing_primary in existing_primary_sections:
                    existing_primary.is_primary_section = False
            section.is_primary_section = is_primary_section

        await session.commit()
        await session.refresh(section)

        section_data: RegisterSectionData = await self._build_register_section_data(section, session)
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
        section: G2PRegisterSection | None = await session.get(G2PRegisterSection, section_id)
        if not section:
            raise ValueError(f"Section with section_id '{section_id}' not found.")

        section.section_ui_schema = section_ui_schema

        await session.commit()
        await session.refresh(section)

        section_data: RegisterSectionData = await self._build_register_section_data(section, session)
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

    async def approve_change_request(self, change_request_id: str, approved_by: str | None = None):
        # Always approve only the requested change request ID.
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            change_request = await session.get(G2PRegisterChangeRequest, change_request_id)
            if not change_request:
                raise ValueError(f"Change request with ID {change_request_id} does not exist.")
            
            section = await session.get(G2PRegisterSection, change_request.section_id)
            if not section:
                raise ValueError(f"Section with ID {change_request.section_id} does not exist.")
            
            if section.is_primary_section and section.section_register_id == section.register_id:
                change_request, _ = await self.approve_primary_master_section_change_request(
                    change_request_id=change_request_id,
                    session=session,
                    skip_verification=False,
                    approved_by=approved_by,
                )
            elif section.section_register_id == section.register_id:
                change_request = await self.approve_non_primary_master_section_change_request(
                    change_request_id=change_request_id,
                    subject_internal_record_id=change_request.internal_record_id,
                    session=session,
                    skip_verification=False,
                    approved_by=approved_by,
                )
            else:
                change_request = await self.approve_child_section_change_request(
                    change_request_id=change_request_id,
                    subject_internal_record_id=change_request.internal_record_id,
                    session=session,
                    skip_verification=False,
                    approved_by=approved_by,
                )
                
            _logger.info(f"Approved change request: {change_request_id}")

            # Enqueue score computations for the change request
            _logger.debug(f"Enqueuing score computations for change_request_id: {change_request_id}")
            g2p_score_compute_service = G2PScoreComputeService.get_component()
            await g2p_score_compute_service.enqueue_score_computations(
                change_request=change_request,
                session=session,
            )
            _logger.debug(f"Finished enqueuing score computations for change_request_id: {change_request_id}")
            
            await session.commit()
            await session.refresh(change_request)
            return change_request

    async def auto_approve_change_request(self, change_request_id: str):
        """Approve a change request while skipping verification-count validation."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            change_request = await self._approve_change_request_core(
                change_request_id=change_request_id,
                session=session,
                skip_verification=True,
            )
            _logger.info(f"Auto-approved change request: {change_request_id}")
            await session.commit()
            await session.refresh(change_request)
            return change_request

    async def auto_approve_primary_master_section_change_request(self, change_request_id: str) -> tuple[G2PRegisterChangeRequest, str]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            change_request, subject_internal_record_id = await self.approve_primary_master_section_change_request(
                change_request_id=change_request_id,
                session=session,
                skip_verification=True,
            )
            _logger.info(f"Auto-approved primary master section change request: {change_request_id}")
            await session.commit()
            await session.refresh(change_request)
            return change_request, subject_internal_record_id

    async def auto_approve_non_primary_master_section_change_request(self, change_request_id: str, subject_internal_record_id: str) -> G2PRegisterChangeRequest:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            change_request = await self.approve_non_primary_master_section_change_request(
                change_request_id=change_request_id,
                subject_internal_record_id=subject_internal_record_id,
                session=session,
                skip_verification=True,
            )
            _logger.info(f"Auto-approved non-primary master section change request: {change_request_id}")
            await session.commit()
            await session.refresh(change_request)
            return change_request

    async def auto_approve_child_section_change_request(self, change_request_id: str, subject_internal_record_id: str) -> G2PRegisterChangeRequest:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            change_request = await self.approve_child_section_change_request(
                change_request_id=change_request_id,
                subject_internal_record_id=subject_internal_record_id,
                session=session,
                skip_verification=True,
            )
            _logger.info(f"Auto-approved child section change request: {change_request_id}")
            await session.commit()
            await session.refresh(change_request)
            return change_request

    async def approve_single_change_request(self, change_request_id: str, session):
        return await self._approve_change_request_core(
            change_request_id=change_request_id,
            session=session,
            skip_verification=False
        )

    async def _approve_change_request_core(
        self,
        change_request_id: str,
        session,
        skip_verification: bool = False,
        skip_sequence_check: bool = False,
        approved_by: str | None = None,
    ):
        # Validate change request exists and is pending approval
        change_request: G2PRegisterChangeRequest = await self.validate_change_request_exists(change_request_id, session)
        # Mark change request as approved
        actor_name = approved_by or "system"
        change_request.approval_status = ApprovalStatusEnum.APPROVED.value
        change_request.approved_by = actor_name
        change_request.approved_at = datetime.now()
        session.add(change_request)
        
        _logger.info(f"Validating change request for approval: {change_request}")
        g2p_register_section = await self.validate_change_request_section(change_request, session)
        # Validate whether verifications are done
        if not skip_verification:
            await self.validate_change_request_verifications(change_request, session)
        # Ensure there are no earlier change requests for the internal_record_id pending approval
        if not skip_sequence_check:
            await self.validate_change_request_sequence(change_request, session)
        # In case of approval, insert data into register_history
        await self.insert_into_register_history(change_request, session)
        # Upsert data into register
        await self.insert_into_register(change_request, session)
        # Handle documents if section.documents_required is True
        if g2p_register_section and g2p_register_section.documents_required:
            await self._handle_documents_on_approval(change_request, g2p_register_section, session)

        # Handle POST APPROVAL domain service operation
        from ..services import G2PRegisterDomainService
        g2p_register_definition = await self.validate_register_definition(change_request.section_register_id, session)

        module = importlib.import_module("openg2p_registry_extensions.register_domain.factory")
        domain_factory_class_name = "G2PRegisterDomainFactory"
        domain_factory_class = getattr(module, domain_factory_class_name)
        g2p_registry_domain_factory = domain_factory_class.get_component()
        # fall back initialization
        if not g2p_registry_domain_factory:
            g2p_registry_domain_factory = domain_factory_class()
        domain_service: G2PRegisterDomainService = g2p_registry_domain_factory.get_domain_service(g2p_register_definition.register_mnemonic)
        if not domain_service:
            raise Exception(f"No domain service found for register mnemonic '{g2p_register_definition.register_mnemonic}'")

        await domain_service.post_approve(change_request, session)

        return change_request        
    
    async def approve_primary_master_section_change_request(
        self,
        change_request_id: str,
        session,
        skip_verification: bool = False,
        skip_sequence_check: bool = False,
        approved_by: str | None = None,
    ) -> tuple[G2PRegisterChangeRequest, str]:
        change_request: G2PRegisterChangeRequest = await self.validate_change_request_exists(change_request_id, session)

        actor_name = approved_by or "system"
        change_request.approval_status = ApprovalStatusEnum.APPROVED.value
        change_request.approved_by = actor_name
        change_request.approved_at = datetime.now()
        session.add(change_request)

        _logger.info(f"Approving primary master section change request: {change_request}")
        g2p_register_section = await self.validate_change_request_core(change_request, session, skip_verification, skip_sequence_check)
        
        # In case of approval, insert data into register_history
        await self.insert_into_register_history(change_request, session)
        # Upsert data into register
        subject_internal_record_id = await self.insert_primary_master_section_into_register(change_request, session)
        # Handle documents if section.documents_required is True
        if g2p_register_section and g2p_register_section.documents_required:
            await self._handle_documents_on_approval(change_request, g2p_register_section, session)
        
        # Handle POST APPROVAL domain service operation
        from ..services import G2PRegisterDomainService
        g2p_register_definition = await self.validate_register_definition(change_request.section_register_id, session)

        module = importlib.import_module("openg2p_registry_extensions.register_domain.factory")
        domain_factory_class_name = "G2PRegisterDomainFactory"
        domain_factory_class = getattr(module, domain_factory_class_name)
        g2p_registry_domain_factory = domain_factory_class.get_component()
        # fall back initialization
        if not g2p_registry_domain_factory:
            g2p_registry_domain_factory = domain_factory_class()
        domain_service: G2PRegisterDomainService = g2p_registry_domain_factory.get_domain_service(g2p_register_definition.register_mnemonic)
        if not domain_service:
            raise Exception(f"No domain service found for register mnemonic '{g2p_register_definition.register_mnemonic}'")

        await domain_service.post_approve(change_request, session)

        return change_request, subject_internal_record_id
    
    async def insert_primary_master_section_into_register(self, change_request: G2PRegisterChangeRequest, session) -> str:
        subject_internal_record_id: str | None = None

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
        change_payload = payload.change_payload[0]

        register_schema_instance = schema_class(**(change_payload or {}))

        existing = (
            await session.execute(
                select(register_class).where(
                    register_class.internal_record_id == change_request.internal_record_id
                )
            )
        ).scalar()

        if change_request.edit_action == EditActionEnum.ADD.value:
            # Build the payload dict excluding None values from schema, then add base fields
            schema_dict = {k: v for k, v in register_schema_instance.dict().items() if v is not None}
            # Use a single canonical internal_record_id for insert + queueing.
            subject_internal_record_id = (
                schema_dict.get("internal_record_id") or change_request.internal_record_id
            )
            schema_dict["internal_record_id"] = subject_internal_record_id

            generate_functional_record_id: bool = await self._check_functional_record_id_generation_required(
                register_definition
            )
            if generate_functional_record_id:
                await self._handle_functional_record_id_generation(
                    register_id=register_definition.register_id,
                    internal_record_id=subject_internal_record_id,
                    session=session,
                )
            schema_dict["functional_record_id"] = (
                str(f"TEMP-{uuid.uuid4().hex}") if generate_functional_record_id else change_payload.get("functional_record_id")
            )
            schema_dict["created_by"] = change_request.created_by
            schema_dict["created_at"] = change_request.created_at
            schema_dict["last_approved_at"] = change_request.approved_at
            schema_dict["last_approved_by"] = change_request.approved_by or "system"

            # Convert date strings to date objects before creating the instance
            schema_dict = self._convert_date_strings_to_objects(schema_dict, register_class)
            
            new_instance = register_class(**schema_dict)
            session.add(new_instance)
        elif change_request.edit_action == EditActionEnum.UPDATE.value and existing:
            subject_internal_record_id = existing.internal_record_id
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
            setattr(existing, "last_approved_by", change_request.approved_by or "system")
        else:
            _logger.error(f"Unknown edit action '{change_request.edit_action}' for change request '{change_request.change_request_id}'")
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.UNKNOWN_CHANGE_REQUEST_ACTION.value[1],
                message=G2PRegistryErrorCodes.UNKNOWN_CHANGE_REQUEST_ACTION.value[0]
            )
        return subject_internal_record_id

    async def approve_non_primary_master_section_change_request(
        self,
        change_request_id: str,
        subject_internal_record_id: str,
        session,
        skip_verification: bool = False,
        skip_sequence_check: bool = False,
        approved_by: str | None = None,
    ) -> G2PRegisterChangeRequest:
        change_request: G2PRegisterChangeRequest = await self.validate_change_request_exists(change_request_id, session)

        actor_name = approved_by or "system"
        change_request.approval_status = ApprovalStatusEnum.APPROVED.value
        change_request.approved_by = actor_name
        change_request.approved_at = datetime.now()
        session.add(change_request)

        _logger.info(f"Approving non primary master section change request: {change_request}")
        g2p_register_section = await self.validate_change_request_core(change_request, session, skip_verification, skip_sequence_check)
        
        # In case of approval, insert data into register_history
        await self.insert_into_register_history(change_request, session)
        # Upsert data into register
        await self.insert_non_primary_master_section_into_register(change_request, subject_internal_record_id, session)
        # Handle documents if section.documents_required is True
        if g2p_register_section and g2p_register_section.documents_required:
            await self._handle_documents_on_approval(change_request, g2p_register_section, session)
        
        # Handle POST APPROVAL domain service operation
        from ..services import G2PRegisterDomainService
        g2p_register_definition = await self.validate_register_definition(change_request.section_register_id, session)

        module = importlib.import_module("openg2p_registry_extensions.register_domain.factory")
        domain_factory_class_name = "G2PRegisterDomainFactory"
        domain_factory_class = getattr(module, domain_factory_class_name)
        g2p_registry_domain_factory = domain_factory_class.get_component()
        # fall back initialization
        if not g2p_registry_domain_factory:
            g2p_registry_domain_factory = domain_factory_class()
        domain_service: G2PRegisterDomainService = g2p_registry_domain_factory.get_domain_service(g2p_register_definition.register_mnemonic)
        if not domain_service:
            raise Exception(f"No domain service found for register mnemonic '{g2p_register_definition.register_mnemonic}'")

        await domain_service.post_approve(change_request, session)

        return change_request
    
    async def insert_non_primary_master_section_into_register(self, change_request: G2PRegisterChangeRequest, subject_internal_record_id: str, session):

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
        
        for change_payload in payload.change_payload:
            register_schema_instance = schema_class(**(change_payload or {}))

            existing = (
                await session.execute(
                    select(register_class).where(
                        register_class.internal_record_id == subject_internal_record_id
                    )
                )
            ).scalar()

            if not existing:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                    message=(
                        f"Subject record not found for internal_record_id '{subject_internal_record_id}' "
                        f"while approving change request '{change_request.change_request_id}'."
                    ),
                )

            if change_payload.get("edit_action") == EditActionEnum.ADD.value or change_payload.get("edit_action") == EditActionEnum.UPDATE.value:
                mapper = inspect(register_class)
                for key, value in register_schema_instance.dict().items():
                    # Only update values in change request payload
                    if key in change_payload:
                        # Keep subject identity immutable across non-primary section approvals.
                        if key in {"internal_record_id", "link_internal_record_id"}:
                            continue
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
                setattr(existing, "last_approved_by", change_request.approved_by or "system")
            else:
                _logger.error(f"Unknown edit action '{change_request.edit_action}' for change request '{change_request.change_request_id}'")
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.UNKNOWN_CHANGE_REQUEST_ACTION.value[1],
                    message=G2PRegistryErrorCodes.UNKNOWN_CHANGE_REQUEST_ACTION.value[0]
                )
    
    async def approve_child_section_change_request(
        self,
        change_request_id: str,
        subject_internal_record_id: str,
        session,
        skip_verification: bool = False,
        skip_sequence_check: bool = False,
        approved_by: str | None = None,
    ) -> G2PRegisterChangeRequest:
        change_request: G2PRegisterChangeRequest = await self.validate_change_request_exists(change_request_id, session)

        actor_name = approved_by or "system"
        change_request.approval_status = ApprovalStatusEnum.APPROVED.value
        change_request.approved_by = actor_name
        change_request.approved_at = datetime.now()
        session.add(change_request)

        _logger.info(f"Approving child section change request: {change_request}")
        g2p_register_section = await self.validate_change_request_core(change_request, session, skip_verification, skip_sequence_check)
        
        # In case of approval, insert data into register_history
        await self.insert_into_register_history(change_request, session)
        # Upsert data into register
        subject_internal_record_id = await self.insert_child_section_into_register(change_request, subject_internal_record_id, session)
        # Handle documents if section.documents_required is True
        if g2p_register_section and g2p_register_section.documents_required:
            await self._handle_documents_on_approval(change_request, g2p_register_section, session)
        
        # Handle POST APPROVAL domain service operation
        from ..services import G2PRegisterDomainService
        g2p_register_definition = await self.validate_register_definition(change_request.section_register_id, session)

        module = importlib.import_module("openg2p_registry_extensions.register_domain.factory")
        domain_factory_class_name = "G2PRegisterDomainFactory"
        domain_factory_class = getattr(module, domain_factory_class_name)
        g2p_registry_domain_factory = domain_factory_class.get_component()
        # Celery workers may not have initialized components; fall back to instantiating.
        if not g2p_registry_domain_factory:
            g2p_registry_domain_factory = domain_factory_class()
        domain_service: G2PRegisterDomainService = g2p_registry_domain_factory.get_domain_service(g2p_register_definition.register_mnemonic)
        if not domain_service:
            raise Exception(f"No domain service found for register mnemonic '{g2p_register_definition.register_mnemonic}'")

        await domain_service.post_approve(change_request, session)

        return change_request

    async def insert_child_section_into_register(self, change_request: G2PRegisterChangeRequest, subject_internal_record_id: str, session):
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
        for change_payload in payload.change_payload:
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
                setattr(existing, "last_approved_by", change_request.approved_by or "system")
            elif change_payload.get("edit_action") == EditActionEnum.ADD.value:
                # Build the payload dict excluding None values from schema, then add base fields
                schema_dict = {k: v for k, v in register_schema_instance.dict().items() if v is not None}
                schema_dict["functional_record_id"] = change_payload.get("functional_record_id") 
                schema_dict["created_by"] = change_request.created_by
                schema_dict["created_at"] = change_request.created_at
                schema_dict["last_approved_at"] = change_request.approved_at
                schema_dict["last_approved_by"] = change_request.approved_by or "system"
                
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
            
    async def _fetch_change_requests_for_intake_form(self, submission_id: str, session) -> list[G2PRegisterChangeRequest]:
        result = await session.execute(
            select(G2PRegisterChangeRequest).where(
                G2PRegisterChangeRequest.submission_id == submission_id
            )
        )
        return result.scalars().all()
    
    async def reject_change_request(
        self,
        change_request_id: str,
        reason: str,
        rejected_by: str | None = None,
    ):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate change request exists and is pending approval
            change_request = await self.validate_change_request_exists(change_request_id, session)
            _logger.info(f"Validated change request for rejection: {change_request}")
            # Mark change request as rejected
            change_request.approval_status = ApprovalStatusEnum.REJECTED.value
            change_request.approved_by = rejected_by or "system"
            change_request.approved_at = datetime.now()
            change_request.rejection_reason = reason
            await session.commit()
            await session.refresh(change_request)
            return change_request

    async def validate_change_request_core(
        self,
        change_request: G2PRegisterChangeRequest,
        session,
        skip_verification: bool = False,
        skip_sequence_check: bool = False,
    ) -> G2PRegisterSection:
        g2p_register_section = await self.validate_change_request_section(change_request, session)
        # Validate whether verifications are done
        if not skip_verification:
            await self.validate_change_request_verifications(change_request, session)
        # Ensure there are no earlier change requests for the internal_record_id pending approval
        if not skip_sequence_check:
            await self.validate_change_request_sequence(change_request, session)
        return g2p_register_section

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
        # TODO: check internal_record_id != null
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
        if register_definition.register_purpose == RegisterPurposeEnum.PROGRAM_REGISTER.value:
            # No history for program intake_forms
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

    async def _check_functional_record_id_generation_required(
        self, register_definition: G2PRegisterDefinition
    ) -> bool:
        return (
            bool(register_definition)
            and register_definition.functional_id_generation_required is True
            and register_definition.register_purpose == RegisterPurposeEnum.REGISTER.value
        )

    async def _handle_functional_record_id_generation(
        self, register_id: str, internal_record_id: str, session
    ) -> None:
        queue_record = G2PFunctionalIdGenerationQueue(
            register_id=register_id,
            internal_record_id=internal_record_id,
        )
        session.add(queue_record)

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
        history_dict["submission_id"] = change_request.submission_id
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

    # TODO: _create_or_update_child_register_record
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
            setattr(existing, "last_approved_by", change_request.approved_by or "system")
        elif change_payload.get("edit_action") == EditActionEnum.ADD.value:
            # Build the payload dict excluding None values from schema, then add base fields
            schema_dict = {k: v for k, v in register_schema_instance.dict().items() if v is not None}
            schema_dict["functional_record_id"] = change_payload.get("functional_record_id") 
            schema_dict["created_by"] = change_request.created_by
            schema_dict["created_at"] = change_request.created_at
            schema_dict["last_approved_at"] = change_request.approved_at
            schema_dict["last_approved_by"] = change_request.approved_by or "system"
            
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

    async def construct_change_request(
        self,
        change_request_request_payload: ChangeRequestRequestPayload,
        g2p_register_section: G2PRegisterSection,
        register_mnemonic: str,
        source_partner_id: str = None,
        submission_id: str = None,
        created_by: str | None = None,
    ) -> G2PRegisterChangeRequest:
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

        serialized_payloads: list[dict] = [item.model_dump() for item in change_request_request_payload.change_payload] if change_request_request_payload.change_payload else []

        register_domain_service: G2PRegisterDomainService | None = self._get_domain_service_by_register_mnemonic(register_mnemonic)
        
        constructed_record_name = self._construct_record_name_for_change_request(register_domain_service, serialized_payloads)

        constructed_search_text = self._construct_search_text_for_change_request(
            register_domain_service,
            serialized_payloads,
            constructed_record_name,
        )

        # Create the payload object - change_payload is now always a list
        change_request_payload_obj = G2PRegisterChangeRequestPayload(
            change_request_id=change_request_id,
            change_payload=serialized_payloads,
            search_text=constructed_search_text,
        )

        # Determine change request source based on submission_id
        change_request_source = ChangeRequestSourceEnum.INTAKE_FORM.value if submission_id else ChangeRequestSourceEnum.DIRECT.value
        no_of_verifications_required = g2p_register_section.no_of_verifications_required if g2p_register_section else 0
        actor_name = created_by or source_partner_id or "system"

        # Create the change request object
        g2p_register_change_request = G2PRegisterChangeRequest(
            change_request_id=change_request_id,
            record_name=constructed_record_name,
            register_id=change_request_request_payload.register_id,
            tab_id=change_request_request_payload.tab_id,
            edit_action=change_request_request_payload.edit_action,
            internal_record_id=internal_record_id,
            section_id=change_request_request_payload.section_id,
            is_primary_section=g2p_register_section.is_primary_section if g2p_register_section else False,
            is_core_section=g2p_register_section.is_core_section if g2p_register_section else False,
            section_register_id=change_request_request_payload.section_register_id,
            source_partner_id=source_partner_id or "system",
            change_request_source=change_request_source,
            submission_id=submission_id,
            created_by=actor_name,
            created_at=datetime.now(),
            no_of_verifications_required=no_of_verifications_required,
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
                    select(func.count()).select_from(register_class).where(register_class.record_status == RecordStatusEnum.ACTIVE.value)
                )
            ).scalar_one()

            return total_record_count
        except (AttributeError, ModuleNotFoundError) as error:
            _logger.warning(f"Could not find register class for mnemonic {register_definition.register_mnemonic}: {str(error)}")
            return 0

    async def _fetch_all_registers(self, session, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[AllRegistersRegisterData], int]:
        """Fetch all registers with pagination, master_register_mnemonic, and has_data fields"""

        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(G2PRegisterDefinition)
        )
        total_items = count_result.scalar_one()

        # Build query with pagination
        query = select(G2PRegisterDefinition)

        # Apply sorting
        if sort_by:
            try:
                if sort_by.startswith('-'):
                    sort_column = getattr(G2PRegisterDefinition, sort_by[1:])
                    query = query.order_by(sort_column.desc())
                else:
                    sort_column = getattr(G2PRegisterDefinition, sort_by)
                    query = query.order_by(sort_column.asc())
            except AttributeError:
                _logger.warning(f"Sort column {sort_by} not found, using default order")
                query = query.order_by(G2PRegisterDefinition.register_rank)
        else:
            query = query.order_by(G2PRegisterDefinition.register_rank)

        # Apply pagination
        offset = (current_page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        register_definitions: list[G2PRegisterDefinition] = (
            await session.execute(query)
        ).scalars().all()

        # Build a mapping of register_id to mnemonic for master_register_mnemonic lookup
        all_register_ids = [rd.master_register_id for rd in register_definitions if rd.master_register_id]
        master_register_mnemonics = {}
        if all_register_ids:
            master_registers = (
                await session.execute(
                    select(G2PRegisterDefinition.register_id, G2PRegisterDefinition.register_mnemonic)
                    .where(G2PRegisterDefinition.register_id.in_(all_register_ids))
                )
            ).all()
            master_register_mnemonics = {r.register_id: r.register_mnemonic for r in master_registers}

        all_registers_list: list[AllRegistersRegisterData] = []

        for register_definition in register_definitions:
            # Get master_register_mnemonic
            master_register_mnemonic = None
            if register_definition.master_register_id:
                master_register_mnemonic = master_register_mnemonics.get(register_definition.master_register_id)

            # Check has_data
            has_data = await self._check_register_has_data(register_definition, session)

            # Get register_purpose value (handle enum)
            register_purpose_value = None
            if register_definition.register_purpose:
                register_purpose_value = register_definition.register_purpose if isinstance(register_definition.register_purpose, str) else register_definition.register_purpose.value

            register_data: AllRegistersRegisterData = AllRegistersRegisterData(
                register_id=register_definition.register_id,
                register_mnemonic=register_definition.register_mnemonic,
                register_subject=register_definition.register_subject,
                register_description=register_definition.register_description,
                master_register_id=register_definition.master_register_id,
                master_register_mnemonic=master_register_mnemonic,
                has_data=has_data,
                register_purpose=register_purpose_value,
                program_id=register_definition.program_id,
                program_mnemonic=register_definition.program_mnemonic,
                register_rank=register_definition.register_rank,
                register_icon=register_definition.register_icon,
                has_image=register_definition.has_image,
                dedup_is_enabled=register_definition.dedup_is_enabled,
                dedup_threshold_score=register_definition.dedup_threshold_score,
                functional_id_generation_required=register_definition.functional_id_generation_required,
            )
            all_registers_list.append(register_data)

        return all_registers_list, total_items

    async def _check_register_has_data(self, register_definition: G2PRegisterDefinition, session) -> bool:
        """Check if a register has data in register table or change_request table (any state)"""
        # 1. Check register table (using dynamic class)
        try:
            module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
            register_class_prefix = "G2PRegister"
            implementation_class_name = f"{register_class_prefix}{register_definition.register_mnemonic}"
            implementation_class = getattr(module, implementation_class_name)

            count_result = await session.execute(
                select(func.count()).select_from(implementation_class).limit(1)
            )
            if count_result.scalar() > 0:
                return True
        except (AttributeError, ModuleNotFoundError):
            # Register may not have implementation class
            pass

        # 2. Check change_request table (any state)
        cr_count_result = await session.execute(
            select(func.count()).select_from(G2PRegisterChangeRequest)
            .where(G2PRegisterChangeRequest.register_id == register_definition.register_id)
            .limit(1)
        )
        if cr_count_result.scalar() > 0:
            return True

        return False

    async def _fetch_dashboard_registers(self, session) -> list[RegisterData]:
        """Fetch all registers for dashboard display (clone of _fetch_all_registers)"""
        register_definitions: list[G2PRegisterDefinition] = (
            await session.execute(
                select(G2PRegisterDefinition)
                .where(G2PRegisterDefinition.register_purpose != RegisterPurposeEnum.TABLE.value)
                .order_by(G2PRegisterDefinition.register_rank)
            )
        ).scalars().all()

        dashboard_registers_list: list[RegisterData] = []

        for register_definition in register_definitions:
            register_data: RegisterData = RegisterData(
                register_id=register_definition.register_id,
                register_mnemonic=register_definition.register_mnemonic,
                register_subject=register_definition.register_subject,
                register_description=register_definition.register_description,
                master_register_id=register_definition.master_register_id,
                functional_id_generation_required=register_definition.functional_id_generation_required,
            )
            dashboard_registers_list.append(register_data)

        return dashboard_registers_list

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
            master_register_id=master_register_definition.master_register_id,
            functional_id_generation_required=master_register_definition.functional_id_generation_required,
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
                tab_order=tab.tab_order,
                used_for_new_intake_form=tab.used_for_new_intake_form,
                no_of_verifications_required=tab.no_of_verifications_required,
                intake_form_name=tab.intake_form_name,
                intake_form_description=tab.intake_form_description,
                intake_form_auto_approve=tab.intake_form_auto_approve,
                is_active=tab.is_active,
            )
            register_tabs_list.append(tab_data)

        return register_tabs_list

    async def _fetch_register_tabs_paginated(
        self,
        register_id: str,
        current_page: int,
        page_size: int,
        session,
        used_for_new_intake_form: bool | None = None,
    ) -> tuple[list[RegisterUITabData], int]:
        """
        Fetch register tabs with pagination.
        Returns (tabs_list, total_count).
        """
        filter_conditions: list = [G2PRegisterUITab.register_id == register_id]
        if used_for_new_intake_form is not None:
            filter_conditions.append(
                G2PRegisterUITab.used_for_new_intake_form == used_for_new_intake_form
            )

        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(G2PRegisterUITab).where(*filter_conditions)
        )
        total_count = count_result.scalar() or 0

        # Calculate offset
        offset = (current_page - 1) * page_size

        # Fetch paginated results
        register_tabs: list[G2PRegisterUITab] = (
            await session.execute(
                select(G2PRegisterUITab)
                .where(*filter_conditions)
                .order_by(G2PRegisterUITab.tab_order)
                .offset(offset)
                .limit(page_size)
            )
        ).scalars().all()

        register_tabs_list: list[RegisterUITabData] = []
        for tab in register_tabs:
            tab_data: RegisterUITabData = RegisterUITabData(
                tab_id=tab.tab_id,
                register_id=tab.register_id,
                tab_label=tab.tab_label,
                tab_order=tab.tab_order,
                used_for_new_intake_form=tab.used_for_new_intake_form,
                no_of_verifications_required=tab.no_of_verifications_required,
                intake_form_name=tab.intake_form_name,
                intake_form_description=tab.intake_form_description,
                intake_form_auto_approve=tab.intake_form_auto_approve,
                is_active=tab.is_active,
            )
            register_tabs_list.append(tab_data)

        return register_tabs_list, total_count
    
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
        
        hierarchical_service = G2PRegisterHierarchicalService.get_component()
        if not hierarchical_service:
            hierarchical_service = G2PRegisterHierarchicalService()

        for record in results:
            enriched_data = await hierarchical_service.enrich_record_hierarchy(
                g2p_register_definition, record, session
            )
            deep_search_results_list.append(DeepSearchResultData(**enriched_data))

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

        # Default to ACTIVE records unless the caller explicitly filters on record_status.
        if not self._has_explicit_record_status_filter(filter_by):
            filter_conditions.append(implementation_class.record_status == "ACTIVE")

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
                foundational_id=result.foundational_id if hasattr(result, 'foundational_id') else None,
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

    def _has_explicit_record_status_filter(self, filter_by: dict | str | None) -> bool:
        """Return True when filter_by explicitly includes record_status."""
        if not filter_by:
            return False

        if isinstance(filter_by, str):
            try:
                filter_by = json.loads(filter_by)
            except json.JSONDecodeError:
                return False

        return isinstance(filter_by, dict) and "record_status" in filter_by

    async def search_in_change_request(self, search_text: str, current_page: int = 1, page_size: int = 10, sort_by: str = None, filter_by: dict = None) -> tuple[list[ChangeRequestSearchResultData], int]:
        """Search in change requests using search_text field with pagination"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            search_results, total_items = await self._search_in_change_request(search_text, current_page, page_size, filter_by, session, sort_by)
            return search_results, total_items

    async def _search_in_change_request(self, search_text: str, current_page: int, page_size: int, filter_by: dict, session, sort_by: str = None) -> tuple[list[ChangeRequestSearchResultData], int]:
        """Helper method to search in change requests with pagination"""
        search_query = f"%{search_text}%"

        # Build base query
        base_query = select(G2PRegisterChangeRequest, G2PRegisterChangeRequestPayload).join(
            G2PRegisterChangeRequestPayload,
            G2PRegisterChangeRequest.change_request_id == G2PRegisterChangeRequestPayload.change_request_id
        ).where(
            G2PRegisterChangeRequestPayload.search_text.ilike(search_query)
        )

        # Apply sorting
        if sort_by:
            if ":" in sort_by:
                sort_field, sort_dir = sort_by.split(":")
            else:
                sort_field, sort_dir = sort_by, "desc"

            if hasattr(G2PRegisterChangeRequest, sort_field):
                sort_column = getattr(G2PRegisterChangeRequest, sort_field)
            elif hasattr(G2PRegisterChangeRequestPayload, sort_field):
                sort_column = getattr(G2PRegisterChangeRequestPayload, sort_field)
            else:
                sort_column = G2PRegisterChangeRequest.created_at

            if sort_dir.lower() == "desc":
                base_query = base_query.order_by(sort_column.desc())
            else:
                base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(G2PRegisterChangeRequest.created_at.desc())

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
                record_name=change_request.record_name,
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
        """Get the number of versions (unique change requests) for a given register, internal_record_id and tab_id across all sections"""
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

            module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
            history_class_prefix = "G2PRegisterHistory"
            register_class_prefix = "G2PRegister"

            # Collect unique change_request_ids and track latest history record across all sections
            unique_change_request_ids: set[str] = set()
            latest_approved_at: datetime = None
            latest_history_record = None

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

                # Get all internal_record_ids to query by traversing the hierarchy
                history_internal_record_ids: list[str] = await self._get_history_internal_record_ids(
                    section_register_id=section_register_id,
                    subject_internal_record_id=internal_record_id,
                    subject_register_id=register_id,
                    session=session
                )
                
                if not history_internal_record_ids:
                    continue

                # Resolve history class for this section register
                history_class_name = f"{history_class_prefix}{section_register_def.register_mnemonic}"
                try:
                    history_class = getattr(module, history_class_name)
                except AttributeError:
                    continue
                
                # Query history records where internal_record_id is in the traversed IDs
                history_records_result = await session.execute(
                    select(history_class).where(
                        history_class.tab_id == tab_id,
                        history_class.internal_record_id.in_(history_internal_record_ids)
                    )
                )
                history_records = history_records_result.scalars().all()
                
                # Collect unique change_request_ids and track latest record
                for history_record in history_records:
                    unique_change_request_ids.add(history_record.change_request_id)
                    # Track the most recent history record by approved_at
                    if history_record.approved_at:
                        if latest_approved_at is None or history_record.approved_at > latest_approved_at:
                            latest_approved_at = history_record.approved_at
                            latest_history_record = history_record

            # Count unique change requests (not raw history records)
            number_of_versions = len(unique_change_request_ids)

            # Get last_updated_by and last_updated_at from the subject register record
            register_class_name = f"{register_class_prefix}{register_definition.register_mnemonic}"
            register_class = getattr(module, register_class_name)
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

            # Get last_approved_by and last_approved_at from the latest history record across all sections
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
                'is_primary_section', 'submission_id', 'change_request_source', 'created_by', 'created_at',
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
                    'submission_id': history_record.submission_id,
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

                # Get all internal_record_ids to query by traversing the hierarchy
                # This handles multi-level hierarchies (e.g., Farmer → Lands → Crops)
                history_internal_record_ids: list[str] = await self._get_history_internal_record_ids(
                    section_register_id=section_register_id,
                    subject_internal_record_id=internal_record_id,
                    subject_register_id=register_id,
                    session=session
                )
                
                if not history_internal_record_ids:
                    continue

                # Resolve history class for this section register
                history_class_name = f"{history_class_prefix}{section_register_def.register_mnemonic}"
                try:
                    history_class = getattr(module, history_class_name)
                except AttributeError:
                    continue
                
                # Query history records where internal_record_id is in the traversed IDs
                history_records_result = await session.execute(
                    select(history_class).where(
                        history_class.tab_id == tab_id,
                        history_class.internal_record_id.in_(history_internal_record_ids)
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

                # Get all internal_record_ids to query by traversing the hierarchy
                # This handles multi-level hierarchies (e.g., Farmer → Lands → Crops)
                history_internal_record_ids: list[str] = await self._get_history_internal_record_ids(
                    section_register_id=section.section_register_id,
                    subject_internal_record_id=internal_record_id,
                    subject_register_id=register_id,
                    session=session
                )
                
                if not history_internal_record_ids:
                    continue
                
                # Resolve history class for this section register
                history_class_name = f"{history_class_prefix}{section_register_def.register_mnemonic}"
                try:
                    history_class = getattr(module, history_class_name)
                except AttributeError:
                    continue
                
                # Query history records where internal_record_id is in the traversed IDs
                history_records_result = await session.execute(
                    select(history_class).where(
                        history_class.tab_id == tab_id,
                        history_class.internal_record_id.in_(history_internal_record_ids)
                    ).where(
                        func.date(history_class.created_at) == date.fromisoformat(truncated_created_date)
                    ).where(
                        history_class.section_id == section.section_id
                    )
                    .order_by(history_class.created_at.desc())
                )
                history_records = history_records_result.scalars().all()
                
                # Build changes list, deduplicating by change_request_id
                # (Multiple records may share the same change_request_id in hierarchical queries)
                seen_change_requests: dict[str, VersionForDateData] = {}
                for history_record in history_records:
                    if history_record.change_request_id not in seen_change_requests:
                        seen_change_requests[history_record.change_request_id] = VersionForDateData(
                            change_request_id=history_record.change_request_id,
                            created_at=history_record.created_at.isoformat()
                        )
                section_changes = list(seen_change_requests.values())
                
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
                    record_name=change_request.record_name,
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
                record_name=change_request.record_name,
                register_id=change_request.register_id,
                tab_id=change_request.tab_id,
                internal_record_id=change_request.internal_record_id,
                section_id=change_request.section_id,
                section_mnemonic=change_request.section_mnemonic,
                is_primary_section=change_request.is_primary_section,
                is_core_section=change_request.is_core_section,
                section_register_id=change_request.section_register_id,
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

                    # If approval_status is APPROVED, fetch previous history (before this change was applied)
                    if change_request.approval_status == ApprovalStatusEnum.APPROVED.value:
                        # Fetch from history table - get the previous record before this change request
                        history_class_prefix: str = "G2PRegisterHistory"
                        history_class_name: str = f"{history_class_prefix}{g2p_register_definition.register_mnemonic}"
                        history_class = getattr(module, history_class_name)

                        # Get internal_record_ids from change_payloads
                        internal_record_ids = [
                            cp.get("internal_record_id") for cp in change_payloads
                            if cp.get("internal_record_id")
                        ]

                        # Base history fields to exclude from current_register_data
                        history_base_fields: set = {
                            'history_record_id', 'change_request_id', 'tab_id', 'section_id',
                            'submission_id', 'change_request_source', 'is_primary_section',
                            'created_by', 'created_at', 'approved_by', 'approved_at', 'search_text'
                        }

                        # For each internal_record_id, fetch the previous history record
                        for internal_record_id in internal_record_ids:
                            previous_history = (
                                await session.execute(
                                    select(history_class).where(
                                        history_class.internal_record_id == internal_record_id,
                                        history_class.approved_at < change_request.approved_at
                                    ).order_by(history_class.approved_at.desc()).limit(1)
                                )
                            ).scalar()

                            if previous_history:
                                # Convert ORM object to dict for current_register_data
                                mapper = inspect(previous_history.__class__)
                                current_register_data = {}

                                for column in mapper.columns:
                                    column_name: str = column.name
                                    if column_name not in history_base_fields:
                                        value = getattr(previous_history, column_name, None)

                                        # Convert datetime objects to strings
                                        if value is not None and hasattr(value, 'isoformat'):
                                            value = value.isoformat()

                                        current_register_data[column_name] = value
                                current_register_data_list.append(current_register_data)
                    else:
                        # For PENDING/REJECTED, fetch from live register table
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
            record_name=change_request.record_name,
            register_id=change_request.register_id,
            tab_id=change_request.tab_id,
            internal_record_id=change_request.internal_record_id,
            section_id=change_request.section_id,
            section_mnemonic=g2p_register_section.section_mnemonic,
            is_list=g2p_register_section.is_list,
            is_primary_section=change_request.is_primary_section,
            is_core_section=change_request.is_core_section,
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
                "record_name": change_request.record_name,
                "register_id": change_request.register_id,
                "tab_id": change_request.tab_id,
                "internal_record_id": change_request.internal_record_id,
                "section_id": change_request.section_id,
                "section_mnemonic": g2p_register_section.section_mnemonic,
                "is_primary_section": change_request.is_primary_section,
                "is_core_section": change_request.is_core_section,
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
        """Deprecated delegator. Use G2PRegisterVerificationService directly."""
        from .g2p_verification_service import G2PRegisterVerificationService

        verification_service = G2PRegisterVerificationService.get_component()
        return await verification_service.get_verifications(
            change_request_id=change_request_id,
            submission_id=None,
            current_page=current_page,
            page_size=page_size,
            sort_by=sort_by,
            filter_by=filter_by,
        )

    async def add_verification_for_change_request(
        self,
        payload: AddVerificationPayload
    ) -> VerificationData:
        """Deprecated delegator. Use G2PRegisterVerificationService directly."""
        from .g2p_verification_service import G2PRegisterVerificationService

        verification_service = G2PRegisterVerificationService.get_component()
        return await verification_service.add_verification(payload)

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

    async def get_register_tab_sections(
        self,
        register_id: str,
        tab_id: str,
        current_page: int = 1,
        page_size: int = 10
    ) -> tuple[list[RegisterSectionData], int]:
        """
        Get register sections for a given register_id and tab_id with pagination.
        Returns a tuple of (sections list, total_count) from g2p_register_sections table
        filtered by both register_id and tab_id.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            await self.validate_register_definition(register_id, session)

            # Fetch register sections filtered by tab_id with pagination
            register_tab_sections_list, total_count = await self._fetch_register_tab_sections_paginated(
                register_id, tab_id, current_page, page_size, session
            )
            return register_tab_sections_list, total_count

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

    async def get_register_section_ui_schema(self, section_id: str) -> RegisterSectionUISchemaData:
        """
        Get the UI schema for a register section by section_id.
        Returns only the section_id and section_ui_schema fields.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            section = await session.get(G2PRegisterSection, section_id)
            if not section:
                raise ValueError(f"Section with section_id '{section_id}' not found.")
            return RegisterSectionUISchemaData(
                section_id=section.section_id,
                section_ui_schema=section.section_ui_schema
            )

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
        # Fetch the main register definition once (for register_relation computation)
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == register_id
                )
            )
        ).scalar()
        
       
        for section in sections:
            section_register_definition: G2PRegisterDefinition = (
                await session.execute(
                    select(G2PRegisterDefinition).where(
                        G2PRegisterDefinition.register_id == section.section_register_id
                    )
                )
            ).scalar()
            register_relation = await self._get_register_relation(
                register_id=register_id,
                section_register_id=section.section_register_id,
                register_definition=register_definition,
                section_register_definition=section_register_definition,
                session=session
            )
            section_data = await self._build_register_section_data(
                section=section,
                session=session,
                register_purpose=section_register_definition.register_purpose,
                register_relation=register_relation,
            )
            sections_list.append(section_data)

        return sections_list

    async def _get_register_relation(
        self,
        register_id: str,
        section_register_id: str,
        register_definition: G2PRegisterDefinition,
        section_register_definition: G2PRegisterDefinition,
        session
    ) -> RegisterRelationEnum:
        """
        Determine the relationship between section's register and the queried register.
        
        Args:
            register_id: The register_id from the API request
            section_register_id: The section's register_id
            register_definition: The G2PRegisterDefinition for register_id
            section_register_definition: The G2PRegisterDefinition for section_register_id
            session: Database session for async operations
        
        Returns:
            RegisterRelationEnum: SELF, DESCENDANT, DESCENDANT_OF_A_REGISTER, ANCESTOR, or PEER
        """
        if section_register_id == register_id:
            return RegisterRelationEnum.SELF
        
        # Direct child: section's register has this register as its master
        if section_register_definition.master_register_id == register_id:
            return RegisterRelationEnum.DESCENDANT
        
        # Check for indirect descendant (through TABLE-only or with REGISTER in between)
        path_exists, has_register_in_between = await self._has_register_in_path(
            section_register_id, register_id, session
        )
        if path_exists and has_register_in_between:
            return RegisterRelationEnum.DESCENDANT_OF_A_REGISTER
        if path_exists:
            return RegisterRelationEnum.DESCENDANT
        
        # Direct parent: this register has section's register as its master
        if register_definition.master_register_id == section_register_id:
            return RegisterRelationEnum.ANCESTOR
        
        # Peer: both share the same master_register_id
        if (register_definition.master_register_id and 
            register_definition.master_register_id == section_register_definition.master_register_id):
            return RegisterRelationEnum.PEER
        
        # Default fallback (shouldn't happen in normal cases)
        return RegisterRelationEnum.SELF

    async def _has_register_in_path(
        self,
        start_register_id: str,
        target_register_id: str,
        session,
        max_depth: int = 20
    ) -> tuple[bool, bool]:
        """
        Check if there's a path from start to target via master_register_id.
        
        Traverses from start_register_id up via master_register_id.
        Returns:
            tuple[bool, bool]: (path_exists, has_register_in_between)
            - path_exists: True if a path from start to target was found
            - has_register_in_between: True if at least one intermediate node
              has register_purpose = REGISTER
        """
        current_id: str | None = start_register_id
        depth: int = 0
        found_register_in_between: bool = False
        is_first: bool = True  # Skip the starting node

        while current_id and depth < max_depth:
            register_definition: G2PRegisterDefinition = (
                await session.execute(
                    select(G2PRegisterDefinition).where(
                        G2PRegisterDefinition.register_id == current_id
                    )
                )
            ).scalar()

            if not register_definition:
                return False, False
            
            # Move to parent
            current_id = register_definition.master_register_id
            
            if is_first:
                is_first = False
                depth += 1
                continue
            
            # Check if we reached the target
            if register_definition.register_id == target_register_id:
                return True, found_register_in_between
            
            # Check if current intermediate node is a REGISTER
            if register_definition.register_purpose == RegisterPurposeEnum.REGISTER.value:
                found_register_in_between = True
            
            # Check if parent is the target
            if current_id == target_register_id:
                return True, found_register_in_between
                
            depth += 1

        return False, False

    async def _fetch_register_tab_sections(self, register_id: str, tab_id: str, session) -> list[RegisterSectionData]:
        """Fetch register sections from g2p_register_sections table filtered by tab_id."""
        result = await session.execute(
            select(G2PRegisterSection).where(
                G2PRegisterSection.register_id == register_id,
                G2PRegisterSection.tab_id == tab_id
            )
        )
        sections = result.scalars().all()

        # Fetch the main register definition once (for register_relation computation)
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == register_id
                )
            )
        ).scalar()

        sections_list: list[RegisterSectionData] = []
        for section in sections:
            # Get section's register definition for register_purpose and register_relation
            if section.section_register_id == register_id:
                # Same register - reuse the main register definition
                section_register_definition = register_definition
            else:
                # Different register - fetch section's register definition
                section_register_definition: G2PRegisterDefinition = (
                    await session.execute(
                        select(G2PRegisterDefinition).where(
                            G2PRegisterDefinition.register_id == section.section_register_id
                        )
                    )
                ).scalar()

            # Determine the relationship between section's register and the main register
            register_relation = await self._get_register_relation(
                register_id=register_id,
                section_register_id=section.section_register_id,
                register_definition=register_definition,
                section_register_definition=section_register_definition,
                session=session
            )

            section_data = await self._build_register_section_data(
                section=section,
                session=session,
                register_purpose=section_register_definition.register_purpose,
                register_relation=register_relation,
            )
            sections_list.append(section_data)

        return sections_list

    async def _fetch_register_tab_sections_paginated(
        self,
        register_id: str,
        tab_id: str,
        current_page: int,
        page_size: int,
        session
    ) -> tuple[list[RegisterSectionData], int]:
        """Fetch register sections from g2p_register_sections table filtered by tab_id with pagination."""
        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(G2PRegisterSection).where(
                G2PRegisterSection.register_id == register_id,
                G2PRegisterSection.tab_id == tab_id
            )
        )
        total_count = count_result.scalar() or 0

        # Calculate offset
        offset = (current_page - 1) * page_size

        # Fetch paginated results
        result = await session.execute(
            select(G2PRegisterSection).where(
                G2PRegisterSection.register_id == register_id,
                G2PRegisterSection.tab_id == tab_id
            ).order_by(G2PRegisterSection.section_order)
            .offset(offset)
            .limit(page_size)
        )
        sections = result.scalars().all()

        # Fetch the main register definition once (for register_relation computation)
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == register_id
                )
            )
        ).scalar()

        sections_list: list[RegisterSectionData] = []
        for section in sections:
            # Get section's register definition for register_purpose and register_relation
            if section.section_register_id == register_id:
                # Same register - reuse the main register definition
                section_register_definition = register_definition
            else:
                # Different register - fetch section's register definition
                section_register_definition: G2PRegisterDefinition = (
                    await session.execute(
                        select(G2PRegisterDefinition).where(
                            G2PRegisterDefinition.register_id == section.section_register_id
                        )
                    )
                ).scalar()

            # Determine the relationship between section's register and the main register
            register_relation = await self._get_register_relation(
                register_id=register_id,
                section_register_id=section.section_register_id,
                register_definition=register_definition,
                section_register_definition=section_register_definition,
                session=session
            )

            section_data = await self._build_register_section_data(
                section=section,
                session=session,
                register_purpose=section_register_definition.register_purpose,
                register_relation=register_relation,
            )
            sections_list.append(section_data)

        return sections_list, total_count

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
        
        # Fetch the main register definition once (for register_relation computation)
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == register_id
                )
            )
        ).scalar()
        
        section_register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == section.section_register_id
                )
            )
        ).scalar()
        
        register_relation = await self._get_register_relation(
                register_id=register_id,
                section_register_id=section.section_register_id,
                register_definition=register_definition,
                section_register_definition=section_register_definition,
                session=session
            )

        return await self._build_register_section_data(
            section=section,
            session=session,
            register_purpose=section_register_definition.register_purpose,
            register_relation=register_relation,
        )

    async def create_register(
        self,
        register_mnemonic: str,
        register_description: str | None = None,
        master_register_id: str | None = None,
        dedup_is_enabled: bool = False,
        dedup_threshold_score: float | None = None,
        register_icon: str | None = None,
        register_rank: int | None = None,
        register_purpose: str | None = None,
        functional_id_generation_required: bool = False,
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

            # Validate master_register_id exists if provided
            if master_register_id:
                master_register = await session.get(G2PRegisterDefinition, master_register_id)
                if not master_register:
                    raise ValueError(f"Master register with id '{master_register_id}' does not exist.")

            # Create the register definition
            register_id: str = str(uuid.uuid4())
            register_definition = G2PRegisterDefinition(
                register_id=register_id,
                register_mnemonic=register_mnemonic,
                register_description=register_description,
                master_register_id=master_register_id,
                dedup_is_enabled=dedup_is_enabled,
                dedup_threshold_score=dedup_threshold_score,
                register_icon=register_icon,
                register_rank=register_rank,
                register_purpose=register_purpose if register_purpose else RegisterPurposeEnum.REGISTER.value,
                functional_id_generation_required=functional_id_generation_required,
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
                master_register_id=master_register_id,
                register_purpose=register_definition.register_purpose,
                register_rank=register_definition.register_rank,
                register_icon=register_definition.register_icon,
                functional_id_generation_required=register_definition.functional_id_generation_required,
            )

    async def edit_register(
        self,
        register_id: str,
        register_mnemonic: str | None = None,
        register_description: str | None = None,
        master_register_id: str | None = None,
        dedup_is_enabled: bool | None = None,
        dedup_threshold_score: float | None = None,
        register_icon: str | None = None,
        register_rank: int | None = None,
        register_purpose: str | None = None,
        functional_id_generation_required: bool | None = None,
    ) -> RegisterData:
        """
        Edit an existing register definition.
        If the register has data (in register table or change_request table),
        only register_mnemonic and register_description can be edited.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            register_definition: G2PRegisterDefinition = await self.validate_register_definition(register_id, session)

            # Check if register has data
            has_data = await self._check_register_has_data(register_definition, session)

            if has_data:
                # Register has data — only update allowed (display) fields,
                # silently ignoring restricted fields like register_mnemonic,
                # master_register_id, and register_purpose.
                if register_description is not None:
                    register_definition.register_description = register_description

                if register_icon is not None:
                    register_definition.register_icon = register_icon

                if register_rank is not None:
                    register_definition.register_rank = register_rank
                
                if dedup_is_enabled is not None:
                    register_definition.dedup_is_enabled = dedup_is_enabled

                if dedup_threshold_score is not None:
                    register_definition.dedup_threshold_score = dedup_threshold_score

            else:
                # Allow editing all fields
                if register_mnemonic is not None:
                    # Check if the new mnemonic already exists (for a different register)
                    if register_mnemonic != register_definition.register_mnemonic:
                        existing_register = await session.execute(
                            select(G2PRegisterDefinition).where(
                                G2PRegisterDefinition.register_mnemonic == register_mnemonic,
                                G2PRegisterDefinition.register_id != register_id
                            )
                        )
                        if existing_register.scalar():
                            raise ValueError(f"Register with mnemonic '{register_mnemonic}' already exists.")
                    register_definition.register_mnemonic = register_mnemonic

                if register_description is not None:
                    register_definition.register_description = register_description

                if master_register_id is not None:
                    # Validate master_register_id is not the same as register_id
                    if master_register_id == register_id:
                        raise ValueError("A register cannot be its own master register.")
                    # Validate master_register_id exists
                    master_register = await session.get(G2PRegisterDefinition, master_register_id)
                    if not master_register:
                        raise ValueError(f"Master register with id '{master_register_id}' does not exist.")
                    register_definition.master_register_id = master_register_id

                if dedup_is_enabled is not None:
                    register_definition.dedup_is_enabled = dedup_is_enabled

                if dedup_threshold_score is not None:
                    register_definition.dedup_threshold_score = dedup_threshold_score

                if register_icon is not None:
                    register_definition.register_icon = register_icon

                if register_rank is not None:
                    register_definition.register_rank = register_rank

                if register_purpose is not None:
                    register_definition.register_purpose = register_purpose

                if functional_id_generation_required is not None:
                    register_definition.functional_id_generation_required = functional_id_generation_required

            await session.commit()
            await session.refresh(register_definition)

            _logger.info(f"Updated register definition for register_id: {register_id}")

            return RegisterData(
                register_id=register_definition.register_id,
                register_mnemonic=register_definition.register_mnemonic,
                register_subject=register_definition.register_subject,
                register_description=register_definition.register_description,
                master_register_id=register_definition.master_register_id,
                register_purpose=register_definition.register_purpose,
                register_rank=register_definition.register_rank,
                register_icon=register_definition.register_icon,
                functional_id_generation_required=register_definition.functional_id_generation_required,
            )

    async def delete_register(self, register_id: str) -> RegisterData:
        """
        Delete a register definition if it has no data in register table or change_request table.
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate register exists
            register_definition: G2PRegisterDefinition = await self.validate_register_definition(register_id, session)

            # Check if register has data
            has_data = await self._check_register_has_data(register_definition, session)

            if has_data:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.INVALID_REQUEST.value[1],
                    message=f"Cannot delete register '{register_definition.register_mnemonic}' as it has existing data."
                )

            # Store data for return before deletion
            register_data = RegisterData(
                register_id=register_definition.register_id,
                register_mnemonic=register_definition.register_mnemonic,
                register_subject=register_definition.register_subject,
                register_description=register_definition.register_description,
                master_register_id=register_definition.master_register_id,
                register_purpose=register_definition.register_purpose,
                register_rank=register_definition.register_rank,
                register_icon=register_definition.register_icon,
                functional_id_generation_required=register_definition.functional_id_generation_required,
            )

            # Delete associated register schema
            register_schema = await session.get(G2PRegisterSchema, register_id)
            if register_schema:
                await session.delete(register_schema)

            # Delete register definition
            await session.delete(register_definition)
            await session.commit()

            _logger.info(f"Deleted register definition for register_id: {register_id}")

            return register_data

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

            return await self._build_register_section_data(primary_section, session)

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
                    content_type=document.content_type or "intake_form/octet-stream",
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
        registry_logo: str = None,
        registry_theme_id: str = None,
        registry_language_id: str = None
    ) -> RegistryConfigurationData:
        """Create a new registry configuration"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            if registry_theme_id:
                theme_result = await session.execute(
                    select(G2PRegistryTheme).where(G2PRegistryTheme.theme_id == registry_theme_id)
                )
                if not theme_result.scalar_one_or_none():
                    raise G2PRegistryException(
                        code=G2PRegistryErrorCodes.REGISTRY_THEME_NOT_FOUND.value[1],
                        message=G2PRegistryErrorCodes.REGISTRY_THEME_NOT_FOUND.value[0]
                    )
            if registry_language_id:
                language_result = await session.execute(
                    select(G2PRegistryLanguage).where(G2PRegistryLanguage.language_id == registry_language_id)
                )
                if not language_result.scalar_one_or_none():
                    raise G2PRegistryException(
                        code=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_NOT_FOUND.value[1],
                        message=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_NOT_FOUND.value[0]
                    )

            # Check if configuration already exists
            stmt = select(G2PRegistryConfiguration)
            result = await session.execute(stmt)
            existing_config = result.scalar_one_or_none()

            if existing_config:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_CONFIGURATION_EXISTS.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_CONFIGURATION_EXISTS.value[0]
                )

            configuration_id = str(uuid.uuid4())
            registry_configuration = G2PRegistryConfiguration(
                configuration_id=configuration_id,
                registry_name=registry_name,
                registry_logo=registry_logo,
                registry_theme_id=registry_theme_id,
                registry_language_id=registry_language_id
            )
            session.add(registry_configuration)
            if registry_language_id:
                await self._set_default_language(session, registry_language_id)
            await session.commit()

            return RegistryConfigurationData(
                configuration_id=configuration_id,
                registry_name=registry_name,
                registry_logo=registry_logo,
                registry_theme_id=registry_theme_id,
                registry_language_id=registry_language_id
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
                    code=G2PRegistryErrorCodes.REGISTRY_CONFIGURATION_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_CONFIGURATION_NOT_FOUND.value[0]
                )

            return RegistryConfigurationData(
                configuration_id=registry_configuration.configuration_id,
                registry_name=registry_configuration.registry_name,
                registry_logo=registry_configuration.registry_logo,
                registry_theme_id=registry_configuration.registry_theme_id,
                registry_language_id=registry_configuration.registry_language_id
            )

    async def update_registry_configuration(
        self,
        configuration_id: str,
        registry_name: str = None,
        registry_logo: str = None,
        registry_theme_id: str = None,
        registry_language_id: str = None
    ) -> RegistryConfigurationData:
        """Update the registry configuration"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            if registry_theme_id:
                theme_result = await session.execute(
                    select(G2PRegistryTheme).where(G2PRegistryTheme.theme_id == registry_theme_id)
                )
                if not theme_result.scalar_one_or_none():
                    raise G2PRegistryException(
                        code=G2PRegistryErrorCodes.REGISTRY_THEME_NOT_FOUND.value[1],
                        message=G2PRegistryErrorCodes.REGISTRY_THEME_NOT_FOUND.value[0]
                    )

            if registry_language_id:
                language_result = await session.execute(
                    select(G2PRegistryLanguage).where(G2PRegistryLanguage.language_id == registry_language_id)
                )
                if not language_result.scalar_one_or_none():
                    raise G2PRegistryException(
                        code=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_NOT_FOUND.value[1],
                        message=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_NOT_FOUND.value[0]
                    )

            stmt = select(G2PRegistryConfiguration).where(
                G2PRegistryConfiguration.configuration_id == configuration_id
            )
            result = await session.execute(stmt)
            registry_configuration = result.scalar_one_or_none()

            if not registry_configuration:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_CONFIGURATION_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_CONFIGURATION_NOT_FOUND.value[0]
                )

            if registry_name is not None:
                registry_configuration.registry_name = registry_name
            if registry_logo is not None:
                registry_configuration.registry_logo = registry_logo
            if registry_theme_id is not None:
                registry_configuration.registry_theme_id = registry_theme_id
            if registry_language_id is not None:
                registry_configuration.registry_language_id = registry_language_id
                await self._set_default_language(session, registry_language_id)

            await session.commit()

            return RegistryConfigurationData(
                configuration_id=registry_configuration.configuration_id,
                registry_name=registry_configuration.registry_name,
                registry_logo=registry_configuration.registry_logo,
                registry_theme_id=registry_configuration.registry_theme_id,
                registry_language_id=registry_configuration.registry_language_id
            )

    async def _set_default_language(self, session, language_id: str):
        # Set all languages to False
        await session.execute(
            update(G2PRegistryLanguage).values(is_default=False)
        )

        # Set selected language to True
        await session.execute(
            update(G2PRegistryLanguage)
            .where(G2PRegistryLanguage.language_id == language_id)
            .values(is_default=True)
        )

    async def get_all_themes(self) -> list[RegistryThemeData]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(select(G2PRegistryTheme))
            themes = result.scalars().all()
            registry_theme_data_list: list[RegistryThemeData] = [
                RegistryThemeData(
                    theme_id=theme.theme_id,
                    theme_mnemonic=theme.theme_mnemonic,
                    is_factory_shipped=theme.is_factory_shipped
                )
                for theme in themes
            ]
            return registry_theme_data_list

    async def create_theme(
        self,
        theme_mnemonic: str,
        theme_values: list[ThemeAttributeValueInput]
    ) -> ThemeOperationData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            existing = await session.execute(
                select(G2PRegistryTheme).where(G2PRegistryTheme.theme_mnemonic == theme_mnemonic)
            )
            if existing.scalar_one_or_none():
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_THEME_EXISTS.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_THEME_EXISTS.value[0]
                )

            theme = G2PRegistryTheme(
                theme_mnemonic=theme_mnemonic,
                is_factory_shipped=False
            )
            session.add(theme)
            await session.flush()

            for item in theme_values:
                theme_value = G2PRegistryThemeValue(
                    theme_id=theme.theme_id,
                    attribute_name=RegistryThemeAttributeNameEnum(item.attribute_name),
                    attribute_value=item.attribute_value
                )
                session.add(theme_value)

            await session.commit()
            theme_operation_data: ThemeOperationData = ThemeOperationData(theme_id=theme.theme_id, success=True)
            return theme_operation_data

    async def remove_theme(self, theme_id: str) -> ThemeOperationData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(G2PRegistryTheme).where(G2PRegistryTheme.theme_id == theme_id)
            )
            theme = result.scalar_one_or_none()
            if not theme:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_THEME_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_THEME_NOT_FOUND.value[0]
                )
            if theme.is_factory_shipped:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.FACTORY_THEME_DELETE_NOT_ALLOWED.value[1],
                    message=G2PRegistryErrorCodes.FACTORY_THEME_DELETE_NOT_ALLOWED.value[0]
                )

            values_result = await session.execute(
                select(G2PRegistryThemeValue).where(G2PRegistryThemeValue.theme_id == theme_id)
            )
            for value_row in values_result.scalars().all():
                await session.delete(value_row)

            await session.delete(theme)
            await session.commit()
            theme_operation_data: ThemeOperationData =  ThemeOperationData(theme_id=theme_id, success=True)
            return theme_operation_data

    async def update_theme_values(
        self,
        theme_id: str,
        theme_attribute_values: list[ThemeAttributeValueInput]
    ) -> ThemeOperationData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(G2PRegistryTheme).where(G2PRegistryTheme.theme_id == theme_id)
            )
            theme = result.scalar_one_or_none()
            if not theme:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_THEME_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_THEME_NOT_FOUND.value[0]
                )
            if theme.is_factory_shipped:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.FACTORY_THEME_UPDATE_NOT_ALLOWED.value[1],
                    message=G2PRegistryErrorCodes.FACTORY_THEME_UPDATE_NOT_ALLOWED.value[0]
                )

            existing_values = await session.execute(
                select(G2PRegistryThemeValue).where(G2PRegistryThemeValue.theme_id == theme_id)
            )
            for value_row in existing_values.scalars().all():
                await session.delete(value_row)

            for item in theme_attribute_values:
                session.add(
                    G2PRegistryThemeValue(
                        theme_id=theme_id,
                        attribute_name=RegistryThemeAttributeNameEnum(item.attribute_name),
                        attribute_value=item.attribute_value
                    )
                )

            await session.commit()
            theme_operation_data: ThemeOperationData = ThemeOperationData(theme_id=theme_id, success=True)
            return theme_operation_data

    async def get_theme_values(self, theme_id: str) -> list[RegistryThemeValueData]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            theme_result = await session.execute(
                select(G2PRegistryTheme).where(G2PRegistryTheme.theme_id == theme_id)
            )
            theme = theme_result.scalar_one_or_none()
            if not theme:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_THEME_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_THEME_NOT_FOUND.value[0]
                )

            values_result = await session.execute(
                select(G2PRegistryThemeValue).where(G2PRegistryThemeValue.theme_id == theme_id)
            )
            registry_theme_value_data_list: list[RegistryThemeValueData] = [
                RegistryThemeValueData(
                    theme_value_id=value_row.theme_value_id,
                    theme_id=value_row.theme_id,
                    attribute_name=value_row.attribute_name.value,
                    attribute_value=value_row.attribute_value
                )
                for value_row in values_result.scalars().all()
            ]
            return registry_theme_value_data_list

    async def get_all_languages(self) -> list[RegistryLanguageData]:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(select(G2PRegistryLanguage))
            languages = result.scalars().all()
            registry_list_language_data: list[RegistryLanguageData] = [
                RegistryLanguageData(
                    language_id=language.language_id,
                    code=language.code,
                    label=language.label,
                    flag=language.flag,
                    is_default=language.is_default,
                    translation=language.translation,
                )
                for language in languages
            ]
            return registry_list_language_data

    async def get_language(self, language_id: str) -> RegistryLanguageData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)

        async with session_maker() as session:
            result = await session.execute(
                select(G2PRegistryLanguage).where(
                    G2PRegistryLanguage.language_id == language_id
                )
            )
            language = result.scalar_one_or_none()

            if not language:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_NOT_FOUND.value[0]
                )
            registry_language_data: RegistryLanguageData = RegistryLanguageData(
                language_id=language.language_id,
                code=language.code,
                label=language.label,
                flag=language.flag,
                is_default=language.is_default,
                translation=language.translation,
            )
            return registry_language_data

    async def create_language(
        self,
        code: str,
        label: str,
        flag: str = None,
        is_default: bool = False,
        translation: dict = None
    ) -> LanguageOperationData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            existing_registry_language = await session.execute(
                select(G2PRegistryLanguage).where(G2PRegistryLanguage.code == code)
            )
            if existing_registry_language.scalar_one_or_none():
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_EXISTS.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_EXISTS.value[0]
                )

            if is_default:
                default_registry_language = await session.execute(
                    select(G2PRegistryLanguage).where(G2PRegistryLanguage.is_default.is_(True))
                )
                existing_default = default_registry_language.scalar_one_or_none()
                if existing_default:
                    existing_default.is_default = False

            language = G2PRegistryLanguage(
                code=code,
                label=label,
                flag=flag,
                is_default=is_default,
                translation=translation
            )
            session.add(language)
            await session.commit()
            language_operation_data: LanguageOperationData =  LanguageOperationData(language_id=language.language_id, success=True)
            return language_operation_data

    async def update_language(
        self,
        language_id: str,
        code: str = None,
        label: str = None,
        flag: str = None,
        is_default: bool = None,
        translation: dict = None
    ) -> LanguageOperationData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(G2PRegistryLanguage).where(G2PRegistryLanguage.language_id == language_id)
            )
            language = result.scalar_one_or_none()
            if not language:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_NOT_FOUND.value[0]
                )

            if code is not None and code != language.code:
                existing_code_result = await session.execute(
                    select(G2PRegistryLanguage).where(G2PRegistryLanguage.code == code)
                )
                existing_code_language = existing_code_result.scalar_one_or_none()
                if existing_code_language:
                    raise G2PRegistryException(
                        code=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_EXISTS.value[1],
                        message=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_EXISTS.value[0]
                    )
                language.code = code

            if label is not None:
                language.label = label
            if flag is not None:
                language.flag = flag
            if translation is not None:
                language.translation = translation

            if is_default is not None:
                if is_default:
                    default_result = await session.execute(
                        select(G2PRegistryLanguage).where(
                            G2PRegistryLanguage.is_default.is_(True),
                            G2PRegistryLanguage.language_id != language_id
                        )
                    )
                    existing_default = default_result.scalar_one_or_none()
                    if existing_default:
                        existing_default.is_default = False
                language.is_default = is_default

            await session.commit()
            language_operation_data: LanguageOperationData = LanguageOperationData(language_id=language_id, success=True)
            return language_operation_data

    async def remove_language(self, language_id: str) -> LanguageOperationData:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(G2PRegistryLanguage).where(G2PRegistryLanguage.language_id == language_id)
            )
            language = result.scalar_one_or_none()
            if not language:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.REGISTRY_LANGUAGE_NOT_FOUND.value[0]
                )

            await session.delete(language)
            await session.commit()
            language_operation_data: LanguageOperationData = LanguageOperationData(language_id=language_id, success=True)
            return language_operation_data

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
                record_name=change_request.record_name,
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

    async def _find_path_to_ancestor(
        self,
        start_register_id: str,
        target_register_id: str,
        session,
        max_depth: int = 20
    ) -> list[G2PRegisterDefinition] | None:
        """
        Find path from start_register up to target_register via master_register_id.
        
        Args:
            start_register_id: Starting register (child/descendant)
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

    def _get_register_implementation_class(self, register_mnemonic: str, register_purpose: str = None):
        """
        Get implementation class for a register based on its mnemonic.
        
        Args:
            register_mnemonic: The register mnemonic (e.g., "Farmer", "Score")
            register_purpose: The register purpose (e.g., "CORE_TABLE", "REGISTER")
                          If None, will try extensions first, then core
            
        Returns:
            The SQLAlchemy model class for the register
        """
        _logger.info(f"Looking for implementation class for register_mnemonic='{register_mnemonic}' with purpose={register_purpose}")
        
        # If register_purpose is CORE_TABLE, look in core models first
        if register_purpose == RegisterPurposeEnum.CORE_TABLE.value:
            try:
                module = importlib.import_module("openg2p_registry_core.models")
                implementation_class_name = f"G2PRegister{register_mnemonic}"
                
                if hasattr(module, implementation_class_name):
                    implementation_class = getattr(module, implementation_class_name)
                    _logger.info(f"Found core implementation class {implementation_class_name} for {register_mnemonic}")
                    return implementation_class
                else:
                    raise AttributeError(f"Core class {implementation_class_name} not found")
                    
            except (AttributeError, ModuleNotFoundError) as error:
                _logger.error(f"Could not load core class for {register_mnemonic}: {str(error)}")
                raise
        
        # Try extensions for regular registers
        try:
            module = importlib.import_module("openg2p_registry_extensions.register_domain.models")
            register_class_prefix: str = "G2PRegister"
            implementation_class_name: str = f"{register_class_prefix}{register_mnemonic}"
            implementation_class = getattr(module, implementation_class_name)
            _logger.info(f"Found extension implementation class {implementation_class_name} for {register_mnemonic}")
            return implementation_class
        except (AttributeError, ModuleNotFoundError) as error:
            _logger.error(f"Could not find register class for mnemonic {register_mnemonic}: {str(error)}")
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                message=f"Register implementation not found for {register_mnemonic}"
            )

    async def _get_history_internal_record_ids(
        self,
        section_register_id: str,
        subject_internal_record_id: str,
        subject_register_id: str,
        session
    ) -> list[str]:
        """
        Get the internal_record_ids to query for history records by traversing 
        down the register hierarchy from subject to section.
        For CORE_TABLE registers, returns all record IDs without hierarchy traversal.
        
        Example: For Farmer (subject) → Lands → Crops (section)
        - Given farmer's internal_record_id
        - Returns all crop internal_record_ids belonging to that farmer
        
        Args:
            section_register_id: The register ID of the section (e.g., Crops)
            subject_internal_record_id: The subject record's internal_record_id (e.g., Farmer's ID)
            subject_register_id: The subject register ID (e.g., Farmer register)
            session: Database session
            
        Returns:
            List of internal_record_ids to query in history table
        """
        # Get section register definition to check if it's CORE_TABLE
        section_register = await session.get(G2PRegisterDefinition, section_register_id)
        if not section_register:
            _logger.warning(f"Section register {section_register_id} not found")
            return [subject_internal_record_id]
        
        # If section_register is CORE_TABLE, return filtered record IDs (no hierarchy)
        if section_register.register_purpose == RegisterPurposeEnum.CORE_TABLE.value:
            impl_class = self._get_register_implementation_class(section_register.register_mnemonic, section_register.register_purpose)
            result = await session.execute(
                select(impl_class.internal_record_id).where(
                    impl_class.internal_record_id == subject_internal_record_id
                )
            )
            filtered_record_ids = [row[0] for row in result.fetchall()]
            _logger.info(f"CORE_TABLE {section_register.register_mnemonic}: returning {len(filtered_record_ids)} filtered record IDs for subject {subject_internal_record_id}")
            return filtered_record_ids
        
        # If same register, no traversal needed
        if section_register_id == subject_register_id:
            return [subject_internal_record_id]
        
        # Build path from section to subject (section is child, subject is ancestor)
        path: list[G2PRegisterDefinition] | None = await self._find_path_to_ancestor(
            section_register_id, subject_register_id, session
        )
        
        if not path:
            # No hierarchy path found, fall back to single ID
            _logger.warning(
                f"No hierarchy path found from section {section_register_id} to subject {subject_register_id}"
            )
            return [subject_internal_record_id]
        
        # Reverse path to traverse from subject (top) to section (bottom)
        # path is [section, ..., subject], we need [subject, ..., section]
        path_reversed: list[G2PRegisterDefinition] = list(reversed(path))
        
        # Start with subject's internal_record_id
        current_ids: list[str] = [subject_internal_record_id]
        
        # Traverse down the hierarchy (skip first register which is subject)
        for i in range(1, len(path_reversed)):
            register_def: G2PRegisterDefinition = path_reversed[i]
            impl_class = self._get_register_implementation_class(register_def.register_mnemonic, register_def.register_purpose)
            
            # Check if this register supports hierarchical operations
            if not hasattr(impl_class, 'link_internal_record_id'):
                # For CORE_TABLE registers without link_internal_record_id, filter by internal_record_id
                result = await session.execute(
                    select(impl_class.internal_record_id).where(
                        impl_class.internal_record_id.in_(current_ids)
                    )
                )
                child_ids = [row[0] for row in result.fetchall()]
                # For CORE_TABLE registers, continue with filtered IDs
                current_ids = child_ids
                continue
            
            # Find all records where link_internal_record_id is in current_ids
            result = await session.execute(
                select(impl_class.internal_record_id).where(
                    impl_class.link_internal_record_id.in_(current_ids)
                )
            )
            child_ids = [row[0] for row in result.fetchall()]
            
            if not child_ids:
                # No records found at this level
                return []
            
            current_ids = child_ids
        
        return current_ids

    def _get_domain_service_by_register_mnemonic(self, register_mnemonic: str) -> G2PRegisterDomainService | None:
        """Resolve the domain service for a given register mnemonic via the domain factory."""
        try:
            module = importlib.import_module("openg2p_registry_extensions.register_domain.factory")
            domain_factory_class_name = "G2PRegisterDomainFactory"
            domain_factory_class = getattr(module, domain_factory_class_name)
            g2p_registry_domain_factory = domain_factory_class.get_component()
            if not g2p_registry_domain_factory:
                g2p_registry_domain_factory = domain_factory_class()
            return g2p_registry_domain_factory.get_domain_service(register_mnemonic)
        except Exception as error:
            _logger.warning(
                f"Unable to resolve domain service for register mnemonic '{register_mnemonic}': {error}"
            )
            return None

    def _construct_record_name_for_change_request(
        self,
        register_domain_service: G2PRegisterDomainService | None,
        payload: list[dict],
    ) -> str | None:
        """Construct the record_name for a change request using the domain service."""
        for payload_dict in payload:
            if not isinstance(payload_dict, dict):
                continue
            try:
                record_name = register_domain_service.construct_record_name(payload_dict)
                if record_name:
                    return record_name
            except NotImplementedError:
                _logger.info("construct_record_name not implemented for change request domain service.")
                return None
            except Exception as error:
                _logger.warning(f"Could not construct change request record_name: {error}")
                return None
        return None

    def _construct_search_text_for_change_request(
        self,
        register_domain_service: G2PRegisterDomainService | None,
        serialized_payloads: list[dict],
        *args,
    ) -> str:
        """Construct the search_text for a change request payload using the domain service.

        Mirrors the pattern used in G2PIntakeFormService._construct_search_text.
        Extra positional args (e.g. record_name, change_request_id) are forwarded
        to the domain service's construct_search_text as the `extra` list.
        """
        if not serialized_payloads or not register_domain_service:
            return ""
        search_tokens: list[str] = []
        for payload_dict in serialized_payloads:
            if not isinstance(payload_dict, dict):
                continue
            try:
                search_text = register_domain_service.construct_search_text(payload_dict, list(args))
                if search_text:
                    search_tokens.append(search_text.strip())
            except NotImplementedError:
                _logger.info("construct_search_text not implemented for change request domain service.")
                return ""
            except Exception as error:
                _logger.warning(f"Could not construct change request search_text: {error}")
        return " ".join(search_tokens).strip()

    async def _build_register_section_data(
        self,
        section: G2PRegisterSection,
        session,
        register_purpose: str | None = None,
        register_relation: RegisterRelationEnum | None = None,
    ) -> RegisterSectionData:
        """Build RegisterSectionData and enrich it with tab metadata via tab_id."""
        tab: G2PRegisterUITab | dict | None = None
        if section.tab_id:
            tab = await self._get_tab(section.tab_id, session)

        def _tab_value(field_name: str, default=None):
            if tab is None:
                return default
            if isinstance(tab, dict):
                return tab.get(field_name, default)
            return getattr(tab, field_name, default)

        return RegisterSectionData(
            section_register_id=section.section_register_id,
            register_id=section.register_id,
            section_id=section.section_id,
            tab_id=section.tab_id,
            used_for_new_intake_form=bool(_tab_value("used_for_new_intake_form", False)),
            tab_label=_tab_value("tab_label"),
            intake_form_name=_tab_value("intake_form_name"),
            intake_form_description=_tab_value("intake_form_description"),
            section_mnemonic=section.section_mnemonic,
            section_description=section.section_description,
            documents_required=section.documents_required,
            no_of_verifications_required=section.no_of_verifications_required,
            auto_approval=section.auto_approval,
            cr_auto_approve_for_bene_portal=section.cr_auto_approve_for_bene_portal,
            cr_auto_approve_for_agent_portal=section.cr_auto_approve_for_agent_portal,
            cr_auto_approve_for_staff_portal=section.cr_auto_approve_for_staff_portal,
            cr_auto_approve_for_partner=section.cr_auto_approve_for_partner,
            cr_auto_approve_for_intake_form=section.cr_auto_approve_for_intake_form,
            is_list=section.is_list,
            register_purpose=register_purpose,
            is_primary_section=section.is_primary_section,
            is_core_section=section.is_core_section,
            section_order=getattr(section, "section_order", 0),
            section_ui_schema=section.section_ui_schema,
            register_relation=register_relation,
        )
