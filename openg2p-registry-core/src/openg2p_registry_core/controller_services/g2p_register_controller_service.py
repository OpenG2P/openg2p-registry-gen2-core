import logging
from openg2p_fastapi_common.service import BaseService

from openg2p_registry_core.models import G2PRegisterChangeLog
import importlib

from ..services import G2PRegisterService, G2PRegisterDomainService
from ..schemas import (
    ChangeLogRequest, ChangeLogPayload, RegisterSummaryData, RegisterData,
    ChildRegisterData, SearchResultData, ChangeLogSearchResultData,
    NumberOfVersionsData, NumberOfPendingChangeLogsData, ChangeLogData,
    ChangeLogsData, RecordData, VerificationsData, AddVerificationPayload,
    VerificationData, DeduplicationRegisterResultsData, DeduplicationChangelogResultsData,
    DeduplicationRegisterResultData, DeduplicationChangelogResultData,
    SearchRegisterRequest, SearchChangeLogRequest, GetChildRegistersRequest,
    GetNumberOfVersionsRequest, GetNumberOfPendingChangeLogsRequest,
    GetChangeLogsRequest, GetChangeLogRequest, GetRecordRequest,
    GetVerificationsRequest, GetDeduplicationRegisterResultsRequest,
    GetDeduplicationChangelogResultsRequest, AddVerificationRequest,
    GetRegisterSummaryDataRequest, GetAllRegistersRequest,
    GetRegisterSchemaRequest, GetRegisterSectionsRequest,
    RegisterSchemaData, RegisterSectionData
)

_logger = logging.getLogger('g2p-register-controller-service')

class G2PRegisterControllerService(BaseService):
    
    async def create_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogPayload:
        _logger.info("Creating change log through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        change_log_payload: ChangeLogPayload = change_log_request.request_body.request_payload

        module = importlib.import_module("openg2p_registry_extensions.register_domain.factory")
        domain_factory_class_name = "G2PRegisterDomainFactory"
        g2p_registry_domain_factory = getattr(module, domain_factory_class_name).get_component()
        domain_service: G2PRegisterDomainService = g2p_registry_domain_factory.get_domain_service(change_log_payload.register_mnemonic)
        print(f"Validating domain attributes for register mnemonic: {change_log_payload.register_mnemonic}")
        await domain_service.validate_domain_attributes(change_log_payload)

        g2p_register_change_log: G2PRegisterChangeLog = await g2p_register_service.create_change_log(
            change_log_payload=change_log_payload,
            source_partner_id=change_log_request.request_header.sender_app_mnemonic
        )

        enriched_change_log_payload: ChangeLogPayload = await self._enrich_change_log_payload(change_log_payload, g2p_register_change_log)

        return enriched_change_log_payload

    async def approve_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogPayload:
        change_log_id = change_log_request.request_body.request_payload.change_log_id
        _logger.info(f"Approving change log with change_log_id: {change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        g2p_register_change_log: G2PRegisterChangeLog = await g2p_register_service.approve_change_log(change_log_id)
        change_log_payload: ChangeLogPayload = ChangeLogPayload()
        enriched_change_log_payload: ChangeLogPayload = await self._enrich_change_log_payload(change_log_payload, g2p_register_change_log)
        return enriched_change_log_payload

    async def reject_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogPayload:
        change_log_id = change_log_request.request_body.request_payload.change_log_id
        rejection_reason: str = getattr(change_log_request.request_body.request_payload, 'rejection_reason', None)
        _logger.info(f"Rejecting change log with change_log_id: {change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        g2p_register_change_log: G2PRegisterChangeLog = await g2p_register_service.reject_change_log(change_log_id, rejection_reason)
        change_log_payload: ChangeLogPayload = ChangeLogPayload()
        enriched_change_log_payload: ChangeLogPayload = await self._enrich_change_log_payload(change_log_payload, g2p_register_change_log)
        return enriched_change_log_payload

    async def get_register_summary_data(self, get_register_summary_data_request: GetRegisterSummaryDataRequest) -> list[RegisterSummaryData]:
        _logger.info("Fetching register summary data through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        register_summary_data_list: list[RegisterSummaryData] = await g2p_register_service.get_register_summary_data()
        return register_summary_data_list

    async def get_all_registers(self, get_all_registers_request: GetAllRegistersRequest) -> list[RegisterData]:
        _logger.info("Fetching all registers through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        all_registers_list: list[RegisterData] = await g2p_register_service.get_all_registers()
        return all_registers_list

    async def get_child_registers(self, get_child_registers_request: GetChildRegistersRequest) -> list[ChildRegisterData]:
        _logger.info(f"Fetching child registers for register_id: {get_child_registers_request.request_body.request_payload.register_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        register_id = get_child_registers_request.request_body.request_payload.register_id
        child_registers_list: list[ChildRegisterData] = await g2p_register_service.get_child_registers(register_id)
        return child_registers_list

    async def search_in_a_register(self, search_register_request: SearchRegisterRequest) -> tuple[list[SearchResultData], int, int]:
        payload = search_register_request.request_body.request_payload
        pagination = search_register_request.request_body.pagination_request
        register_id = payload.register_id

        _logger.info(f"Searching in register_id: {register_id} with search_text: {pagination.search_text}, page: {pagination.current_page}, page_size: {pagination.page_size} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        search_results_list, total_items = await g2p_register_service.search_in_a_register(
            register_id, pagination.search_text, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )

        # Calculate number of pages
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0

        return search_results_list, total_items, number_of_pages

    async def search_in_change_log(self, search_change_log_request: SearchChangeLogRequest) -> tuple[list[ChangeLogSearchResultData], int, int]:
        pagination = search_change_log_request.request_body.pagination_request
        _logger.info(f"Searching in change logs with search_text: {pagination.search_text} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        search_results_list, total_items = await g2p_register_service.search_in_change_log(
            pagination.search_text, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return search_results_list, total_items, number_of_pages

    async def get_number_of_versions(self, get_number_of_versions_request: GetNumberOfVersionsRequest) -> NumberOfVersionsData:
        register_id = get_number_of_versions_request.request_body.request_payload.register_id
        internal_record_id = get_number_of_versions_request.request_body.request_payload.internal_record_id
        _logger.info(f"Getting number of versions for register_id: {register_id}, internal_record_id: {internal_record_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        number_of_versions_data: NumberOfVersionsData = await g2p_register_service.get_number_of_versions(register_id, internal_record_id)
        return number_of_versions_data

    async def get_number_of_pending_change_logs(self, get_number_of_pending_change_logs_request: GetNumberOfPendingChangeLogsRequest) -> NumberOfPendingChangeLogsData:
        register_id = get_number_of_pending_change_logs_request.request_body.request_payload.register_id
        internal_record_id = get_number_of_pending_change_logs_request.request_body.request_payload.internal_record_id
        _logger.info(f"Getting number of pending change logs for register_id: {register_id}, internal_record_id: {internal_record_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        number_of_pending_change_logs_data: NumberOfPendingChangeLogsData = await g2p_register_service.get_number_of_pending_change_logs(register_id, internal_record_id)
        return number_of_pending_change_logs_data

    async def get_change_logs(self, get_change_logs_request: GetChangeLogsRequest) -> tuple[list[ChangeLogData], int, int]:
        payload = get_change_logs_request.request_body.request_payload
        pagination = get_change_logs_request.request_body.pagination_request
        register_id = payload.register_id
        internal_record_id = payload.internal_record_id
        _logger.info(f"Getting change logs for register_id: {register_id}, internal_record_id: {internal_record_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        change_logs_list, total_items = await g2p_register_service.get_change_logs(
            register_id, internal_record_id, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return change_logs_list, total_items, number_of_pages

    async def get_change_log(self, get_change_log_request: GetChangeLogRequest) -> ChangeLogData:
        change_log_id = get_change_log_request.request_body.request_payload.change_log_id
        _logger.info(f"Getting change log for change_log_id: {change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        change_log_data: ChangeLogData = await g2p_register_service.get_change_log(change_log_id)
        return change_log_data

    async def _enrich_change_log_payload(self, change_log_payload: ChangeLogPayload , g2p_register_change_log: G2PRegisterChangeLog) -> ChangeLogPayload:
        
        change_log_payload.change_log_id = g2p_register_change_log.change_log_id
        change_log_payload.approval_status = g2p_register_change_log.approval_status
        change_log_payload.no_of_verifications_required = g2p_register_change_log.no_of_verifications_required
        change_log_payload.no_of_verifications_done = g2p_register_change_log.no_of_verifications_done
        change_log_payload.internal_record_id = g2p_register_change_log.internal_record_id
        change_log_payload.created_by = g2p_register_change_log.created_by
        change_log_payload.created_at = str(g2p_register_change_log.created_at)
        change_log_payload.approved_by = g2p_register_change_log.approved_by
        change_log_payload.approved_at = str(g2p_register_change_log.approved_at) if g2p_register_change_log.approved_at else None

        return change_log_payload

    async def get_record(self, get_record_request: GetRecordRequest) -> RecordData:
        register_id = get_record_request.request_body.request_payload.register_id
        internal_record_id = get_record_request.request_body.request_payload.internal_record_id
        _logger.info(f"Getting record for register_id: {register_id}, internal_record_id: {internal_record_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        record_data: RecordData = await g2p_register_service.get_record(register_id, internal_record_id)
        return record_data

    async def get_verifications_for_change_log(self, get_verifications_request: GetVerificationsRequest) -> tuple[list[VerificationData], int, int]:
        payload = get_verifications_request.request_body.request_payload
        pagination = get_verifications_request.request_body.pagination_request
        change_log_id = payload.change_log_id
        _logger.info(f"Getting verifications for change_log_id: {change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        verifications_list, total_items = await g2p_register_service.get_verifications_for_change_log(
            change_log_id, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return verifications_list, total_items, number_of_pages

    async def add_verification_for_change_log(self, add_verification_request: AddVerificationRequest) -> VerificationData:
        add_verification_payload: AddVerificationPayload = add_verification_request.request_body.request_payload
        _logger.info(f"Adding verification for change_log_id: {add_verification_payload.change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        verification_data: VerificationData = await g2p_register_service.add_verification_for_change_log(add_verification_payload)
        return verification_data

    async def get_deduplication_register_results(self, get_deduplication_register_results_request: GetDeduplicationRegisterResultsRequest) -> tuple[list[DeduplicationRegisterResultData], int, int]:
        """
        Get deduplication results for a change log against register records.
        """
        payload = get_deduplication_register_results_request.request_body.request_payload
        pagination = get_deduplication_register_results_request.request_body.pagination_request
        change_log_id = payload.change_log_id
        _logger.info(f"Getting deduplication register results for change_log_id: {change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        dedup_results_list, total_items = await g2p_register_service.get_deduplication_register_results(
            change_log_id, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return dedup_results_list, total_items, number_of_pages

    async def get_deduplication_changelog_results(self, get_deduplication_changelog_results_request: GetDeduplicationChangelogResultsRequest) -> tuple[list[DeduplicationChangelogResultData], int, int]:
        """
        Get deduplication results for a change log against other change logs.
        """
        payload = get_deduplication_changelog_results_request.request_body.request_payload
        pagination = get_deduplication_changelog_results_request.request_body.pagination_request
        change_log_id = payload.change_log_id
        _logger.info(f"Getting deduplication changelog results for change_log_id: {change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        dedup_results_list, total_items = await g2p_register_service.get_deduplication_changelog_results(
            change_log_id, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return dedup_results_list, total_items, number_of_pages

    async def get_register_schema(self, get_register_schema_request: GetRegisterSchemaRequest) -> RegisterSchemaData:
        """
        Get register schema configuration for a given register_id.
        """
        payload = get_register_schema_request.request_body.request_payload
        register_id = payload.register_id
        _logger.info(f"Getting register schema for register_id: {register_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        register_schema_data: RegisterSchemaData = await g2p_register_service.get_register_schema(register_id)
        return register_schema_data

    async def get_register_sections(self, get_register_sections_request: GetRegisterSectionsRequest) -> list[RegisterSectionData]:
        """
        Get register sections for a given register_id.
        """
        payload = get_register_sections_request.request_body.request_payload
        register_id = payload.register_id
        _logger.info(f"Getting register sections for register_id: {register_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        register_sections_list: list[RegisterSectionData] = await g2p_register_service.get_register_sections(register_id)
        return register_sections_list