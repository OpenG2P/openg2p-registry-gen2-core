import logging
from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PRegisterDataControllerService
from openg2p_registry_core.schemas import (
    GetNumberOfVersionsRequest,
    GetSubjectRecordRequest,
    GetDeduplicationRegisterResultsRequest,
    GetDeduplicationChangelogResultsRequest,
    NumberOfVersionsResponse, NumberOfVersionsData,
    RecordDataResponse, RecordData, RegisterTabRecordData,
    DeduplicationRegisterResultsDataResponse,
    DeduplicationChangelogResultsDataResponse,
    GetRegisterSectionRequest,
    RegisterSectionData, RegisterSectionDataResponse,
    GetSectionRecordsRequest, SectionRecordsDataResponse,
    GetRegisterTabRecordsRequest, RegisterTabRecordsDataResponse
)

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PRegisterDataController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["G2P Register Data"]
        self.g2p_register_data_controller_service = G2PRegisterDataControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/register"

        self.router.add_api_route(
            "/get_number_of_versions",
            self.get_number_of_versions,
            responses={200: {"model": NumberOfVersionsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_subject_record",
            self.get_subject_record,
            responses={200: {"model": RecordDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_deduplication_register_results",
            self.get_deduplication_register_results,
            responses={200: {"model": DeduplicationRegisterResultsDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_deduplication_changelog_results",
            self.get_deduplication_changelog_results,
            responses={200: {"model": DeduplicationChangelogResultsDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_schema_definition_for_register_section",
            self.get_schema_definition_for_register_section,
            responses={200: {"model": RegisterSectionDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_section_records",
            self.get_section_records,
            responses={200: {"model": SectionRecordsDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_register_tab_records",
            self.get_register_tab_records,
            responses={200: {"model": RegisterTabRecordsDataResponse}},
            methods=["POST"],
        )

    async def get_number_of_versions(self, get_number_of_versions_request: GetNumberOfVersionsRequest) -> NumberOfVersionsResponse:
        try:
            number_of_versions_data: NumberOfVersionsData = await self.g2p_register_data_controller_service.get_number_of_versions(get_number_of_versions_request)
            number_of_versions_response: NumberOfVersionsResponse = self.helper.construct_number_of_versions_success_response(
                number_of_versions_data=number_of_versions_data, g2p_request=get_number_of_versions_request
            )
            return number_of_versions_response
        except Exception as error_exception:
            _logger.error(f"Error in get_number_of_versions: {str(error_exception)}")
            error_response: NumberOfVersionsResponse = self.helper.construct_error_response(error_exception, get_number_of_versions_request)
            return error_response

    async def get_subject_record(self, get_subject_record_request: GetSubjectRecordRequest) -> RecordDataResponse:
        try:
            record_data: RecordData = await self.g2p_register_data_controller_service.get_subject_record(get_subject_record_request)
            record_response: RecordDataResponse = self.helper.construct_record_success_response(
                record_data=record_data, g2p_request=get_subject_record_request
            )
            return record_response
        except Exception as error_exception:
            _logger.error(f"Error in get_subject_record: {str(error_exception)}")
            error_response: RecordDataResponse = self.helper.construct_error_response(error_exception, get_subject_record_request)
            return error_response

    async def get_deduplication_register_results(self, get_deduplication_register_results_request: GetDeduplicationRegisterResultsRequest) -> DeduplicationRegisterResultsDataResponse:
        """
        Get deduplication results for a change log against register records.
        """
        try:
            dedup_results_list, total_items, number_of_pages = await self.g2p_register_data_controller_service.get_deduplication_register_results(get_deduplication_register_results_request)
            dedup_results_response: DeduplicationRegisterResultsDataResponse = self.helper.construct_deduplication_register_results_success_response(
                dedup_results_list=dedup_results_list, g2p_request=get_deduplication_register_results_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return dedup_results_response
        except Exception as error_exception:
            _logger.error(f"Error in get_deduplication_register_results: {str(error_exception)}")
            error_response: DeduplicationRegisterResultsDataResponse = self.helper.construct_error_response(error_exception, get_deduplication_register_results_request)
            return error_response

    async def get_deduplication_changelog_results(self, get_deduplication_changelog_results_request: GetDeduplicationChangelogResultsRequest) -> DeduplicationChangelogResultsDataResponse:
        """
        Get deduplication results for a change log against other change logs.
        """
        try:
            dedup_results_list, total_items, number_of_pages = await self.g2p_register_data_controller_service.get_deduplication_changelog_results(get_deduplication_changelog_results_request)
            dedup_results_response: DeduplicationChangelogResultsDataResponse = self.helper.construct_deduplication_changelog_results_success_response(
                dedup_results_list=dedup_results_list, g2p_request=get_deduplication_changelog_results_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return dedup_results_response
        except Exception as error_exception:
            _logger.error(f"Error in get_deduplication_changelog_results: {str(error_exception)}")
            error_response: DeduplicationChangelogResultsDataResponse = self.helper.construct_error_response(error_exception, get_deduplication_changelog_results_request)
            return error_response

    async def get_schema_definition_for_register_section(self, get_register_section_request: GetRegisterSectionRequest) -> RegisterSectionDataResponse:
        """
        Get schema definition for a specific section of a register.
        """
        try:
            register_section_data: RegisterSectionData = await self.g2p_register_data_controller_service.get_register_section(get_register_section_request)
            register_section_response: RegisterSectionDataResponse = self.helper.construct_register_section_success_response(
                register_section_data=register_section_data, g2p_request=get_register_section_request
            )
            return register_section_response
        except Exception as error_exception:
            _logger.error(f"Error in get_schema_definition_for_register_section: {str(error_exception)}")
            error_response: RegisterSectionDataResponse = self.helper.construct_error_response(error_exception, get_register_section_request)
            return error_response

    async def get_section_records(
        self,
        get_section_records_request: GetSectionRecordsRequest
    ) -> SectionRecordsDataResponse:
        """
        Get records from a section register that are linked to a subject record.
        Traverses the master-child hierarchy between registers.
        If subject_register_id == section_register_id, returns the subject record directly.
        """
        try:
            section_records: list[RecordData] = await self.g2p_register_data_controller_service.get_section_records(
                get_section_records_request
            )
            section_records_response: SectionRecordsDataResponse = self.helper.construct_section_records_success_response(
                section_records=section_records, g2p_request=get_section_records_request
            )
            return section_records_response
        except Exception as error_exception:
            _logger.error(f"Error in get_section_records: {str(error_exception)}")
            error_response: SectionRecordsDataResponse = self.helper.construct_error_response(
                error_exception, get_section_records_request
            )
            return error_response

    async def get_register_tab_records(
        self,
        get_register_tab_records_request: GetRegisterTabRecordsRequest
    ) -> RegisterTabRecordsDataResponse:
        """
        Get all records for a tab, grouped by unique section_register_id.
        Multiple sections with the same section_register_id are deduplicated.
        """
        try:
            tab_records: list[RegisterTabRecordData] = await self.g2p_register_data_controller_service.get_register_tab_records(
                get_register_tab_records_request
            )
            tab_records_response: RegisterTabRecordsDataResponse = self.helper.construct_register_tab_records_success_response(
                tab_records=tab_records, g2p_request=get_register_tab_records_request
            )
            return tab_records_response
        except Exception as error_exception:
            _logger.error(f"Error in get_register_tab_records: {str(error_exception)}")
            error_response: RegisterTabRecordsDataResponse = self.helper.construct_error_response(
                error_exception, get_register_tab_records_request
            )
            return error_response