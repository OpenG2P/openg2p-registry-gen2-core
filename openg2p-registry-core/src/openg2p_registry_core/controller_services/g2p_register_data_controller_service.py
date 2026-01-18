import logging
from openg2p_fastapi_common.service import BaseService

from ..services import G2PRegisterService, G2PRegisterHierarchicalService
from ..schemas import (
    NumberOfVersionsData, RecordData, RegisterTabRecordData,
    RecordHistoryListData,
    DeduplicationRegisterResultData, DeduplicationChangerequestResultData,
    GetNumberOfVersionsRequest, GetSubjectRecordRequest,
    GetRecordHistoryRequest,
    GetDeduplicationRegisterResultsRequest,
    GetDeduplicationChangerequestResultsRequest,
    GetRegisterSectionRequest, RegisterSectionData,
    GetSectionRecordsRequest, GetRegisterTabRecordsRequest
)

_logger = logging.getLogger('g2p-register-data-controller-service')


class G2PRegisterDataControllerService(BaseService):

    async def get_number_of_versions(self, get_number_of_versions_request: GetNumberOfVersionsRequest) -> NumberOfVersionsData:
        register_id = get_number_of_versions_request.request_body.request_payload.register_id
        internal_record_id = get_number_of_versions_request.request_body.request_payload.internal_record_id
        tab_id = get_number_of_versions_request.request_body.request_payload.tab_id
        _logger.info(f"Getting number of versions for register_id: {register_id}, internal_record_id: {internal_record_id}, tab_id: {tab_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        number_of_versions_data: NumberOfVersionsData = await g2p_register_service.get_number_of_versions(register_id, internal_record_id, tab_id)
        return number_of_versions_data

    async def get_record_history(self, get_record_history_request: GetRecordHistoryRequest) -> RecordHistoryListData:
        """Get the history records for a given register, internal_record_id and tab_id"""
        register_id = get_record_history_request.request_body.request_payload.register_id
        internal_record_id = get_record_history_request.request_body.request_payload.internal_record_id
        tab_id = get_record_history_request.request_body.request_payload.tab_id
        _logger.info(f"Getting record history for register_id: {register_id}, internal_record_id: {internal_record_id}, tab_id: {tab_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        record_history_data: RecordHistoryListData = await g2p_register_service.get_record_history(register_id, internal_record_id, tab_id)
        return record_history_data

    async def get_subject_record(self, get_subject_record_request: GetSubjectRecordRequest) -> RecordData:
        subject_register_id = get_subject_record_request.request_body.request_payload.subject_register_id
        subject_record_id = get_subject_record_request.request_body.request_payload.subject_record_id
        _logger.info(f"Getting subject record for subject_register_id: {subject_register_id}, subject_record_id: {subject_record_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        record_data: RecordData = await g2p_register_service.get_record(subject_register_id, subject_record_id)
        return record_data

    async def get_deduplication_register_results(self, get_deduplication_register_results_request: GetDeduplicationRegisterResultsRequest) -> tuple[list[DeduplicationRegisterResultData], int, int]:
        """
        Get deduplication results for a change request against register records.
        """
        payload = get_deduplication_register_results_request.request_body.request_payload
        pagination = get_deduplication_register_results_request.request_body.pagination_request
        change_request_id = payload.change_request_id
        _logger.info(f"Getting deduplication register results for change_request_id: {change_request_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        dedup_results_list, total_items = await g2p_register_service.get_deduplication_register_results(
            change_request_id, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return dedup_results_list, total_items, number_of_pages

    async def get_deduplication_changerequest_results(self, get_deduplication_changerequest_results_request: GetDeduplicationChangerequestResultsRequest) -> tuple[list[DeduplicationChangerequestResultData], int, int]:
        """
        Get deduplication results for a change request against other change requests.
        """
        payload = get_deduplication_changerequest_results_request.request_body.request_payload
        pagination = get_deduplication_changerequest_results_request.request_body.pagination_request
        change_request_id = payload.change_request_id
        _logger.info(f"Getting deduplication changerequest results for change_request_id: {change_request_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        dedup_results_list, total_items = await g2p_register_service.get_deduplication_changerequest_results(
            change_request_id, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return dedup_results_list, total_items, number_of_pages

    async def get_register_section(self, get_register_section_request: GetRegisterSectionRequest) -> RegisterSectionData:
        """
        Get a single register section for a given register_id and section_id.
        """
        payload = get_register_section_request.request_body.request_payload
        register_id: str = payload.register_id
        section_id: str = payload.section_id
        _logger.info(f"Getting register section for register_id: {register_id}, section_id: {section_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        register_section_data: RegisterSectionData = await g2p_register_service.get_register_section(register_id, section_id)
        return register_section_data

    async def get_section_records(
        self,
        get_section_records_request: GetSectionRecordsRequest
    ) -> list[RecordData]:
        """
        Get records from a related register that are linked to a subject record.
        Traverses the master-child hierarchy between registers.
        If subject_register_id == section_register_id, returns the subject record directly.
        """
        payload = get_section_records_request.request_body.request_payload
        subject_register_id: str = payload.subject_register_id
        subject_record_id: str = payload.subject_record_id
        section_register_id: str = payload.section_register_id
        _logger.info(
            f"Getting section records for subject_register_id: {subject_register_id}, "
            f"subject_record_id: {subject_record_id}, section_register_id: {section_register_id} "
            f"through controller service"
        )
        g2p_register_hierarchical_service = G2PRegisterHierarchicalService.get_component()
        section_records: list[RecordData] = await g2p_register_hierarchical_service.get_section_records(
            subject_register_id, subject_record_id, section_register_id
        )
        return section_records

    async def get_tab_records(
        self,
        get_register_tab_records_request: GetRegisterTabRecordsRequest
    ) -> list[RegisterTabRecordData]:
        """
        Get all records for a tab, grouped by unique section_register_id.
        Multiple sections with the same section_register_id are deduplicated.
        """
        payload = get_register_tab_records_request.request_body.request_payload
        subject_register_id: str = payload.subject_register_id
        subject_record_id: str = payload.subject_record_id
        tab_id: str = payload.tab_id
        _logger.info(
            f"Getting register tab records for subject_register_id: {subject_register_id}, "
            f"subject_record_id: {subject_record_id}, tab_id: {tab_id} "
            f"through controller service"
        )
        g2p_register_hierarchical_service = G2PRegisterHierarchicalService.get_component()
        tab_records: list[RegisterTabRecordData] = await g2p_register_hierarchical_service.get_tab_records(
            subject_register_id, subject_record_id, tab_id
        )
        return tab_records
