import logging
from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PRegisterControllerService
from openg2p_registry_core.schemas import (
    ChangeLogRequest, ChangeLogResponse, ChangeLogPayload,
    RegisterSummaryDataResponse, RegisterSummaryData,
    ChangeLogSummaryDataResponse, ChangeLogSummaryData,
    AllRegistersResponse, RegisterData,
    ChildRegistersResponse, ChildRegisterData,
    ChildRegisterRequest,
    SearchResultsResponse, SearchResultData,
    SearchRegisterRequest,
    SearchChangeLogRequest,
    GetChildRegistersRequest,
    GetNumberOfVersionsRequest,
    GetNumberOfPendingChangeLogsRequest,
    GetChangeLogsRequest,
    GetChangeLogRequest,
    GetRecordRequest,
    GetVerificationsRequest,
    GetDeduplicationRegisterResultsRequest,
    GetDeduplicationChangelogResultsRequest,
    AddVerificationRequest,
    GetRegisterSummaryDataRequest,
    GetChangeLogSummaryDataRequest,
    GetAllRegistersRequest,
    ChangeLogSearchResultsResponse, ChangeLogSearchResultData,
    NumberOfVersionsResponse, NumberOfVersionsData,
    NumberOfPendingChangeLogsResponse, NumberOfPendingChangeLogsData,
    ChangeLogDataResponse, ChangeLogData,
    ChangeLogsDataResponse, ChangeLogsData,
    RecordDataResponse, RecordData,
    VerificationsDataResponse, VerificationsData,
    VerificationDataResponse, VerificationData,
    AddVerificationPayload,
    DeduplicationRegisterResultsDataResponse,
    DeduplicationChangelogResultsDataResponse,
    GetRegisterSchemaRequest, GetRegisterSectionsRequest,
    RegisterSchemaDataResponse, RegisterSchemaData,
    RegisterSectionsDataResponse, RegisterSectionData
)
from openg2p_fastapi_common.schemas import G2PResponse


from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PRegisterController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["G2P Register"]
        self.g2p_register_controller_service = G2PRegisterControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/register"

        self.router.add_api_route(
            "/create_change_log",
            self.create_change_log,
            responses={200: {"model": ChangeLogResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/approve_change_log",
            self.approve_change_log,
            responses={200: {"model": ChangeLogResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/reject_change_log",
            self.reject_change_log,
            responses={200: {"model": ChangeLogResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_register_summary_data",
            self.get_register_summary_data,
            responses={200: {"model": RegisterSummaryDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_register_changelog_data",
            self.get_register_changelog_data,
            responses={200: {"model": ChangeLogSummaryDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_all_registers",
            self.get_all_registers,
            responses={200: {"model": AllRegistersResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_child_registers",
            self.get_child_registers,
            responses={200: {"model": ChildRegistersResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/search_in_a_register",
            self.search_in_a_register,
            responses={200: {"model": SearchResultsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/search_in_change_log",
            self.search_in_change_log,
            responses={200: {"model": ChangeLogSearchResultsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_number_of_versions",
            self.get_number_of_versions,
            responses={200: {"model": NumberOfVersionsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_number_of_pending_change_logs",
            self.get_number_of_pending_change_logs,
            responses={200: {"model": NumberOfPendingChangeLogsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_change_logs",
            self.get_change_logs,
            responses={200: {"model": ChangeLogsDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_change_log",
            self.get_change_log,
            responses={200: {"model": ChangeLogDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_record",
            self.get_record,
            responses={200: {"model": RecordDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_verifications_for_change_log",
            self.get_verifications_for_change_log,
            responses={200: {"model": VerificationsDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/add_verification_for_change_log",
            self.add_verification_for_change_log,
            responses={200: {"model": VerificationDataResponse}},
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
            "/get_register_schema",
            self.get_register_schema,
            responses={200: {"model": RegisterSchemaDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_register_sections",
            self.get_register_sections,
            responses={200: {"model": RegisterSectionsDataResponse}},
            methods=["POST"],
        )


    async def create_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:
        #TODO: Validate Staff Token here with auth: Annotated[AuthCredentials, Depends(AuthFactory())]

        try:
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.create_change_log(change_log_request)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_payload=change_log_payload, g2p_request=change_log_request
            )
            return change_log_response
        except Exception as error_exception:
            _logger.error(f"Error in create_change_log: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, change_log_request)
            return error_response

    async def approve_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:

        try:
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.approve_change_log(change_log_request)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_payload=change_log_payload, g2p_request=change_log_request
            )
            return change_log_response
        except Exception as error_exception:
            _logger.error(f"Error in approve_change_log: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, change_log_request)
            return error_response

    async def reject_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:
        try:
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.reject_change_log(change_log_request)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_payload=change_log_payload, g2p_request=change_log_request
            )
            return change_log_response
        except Exception as error_exception:
            _logger.error(f"Error in reject_change_log: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, change_log_request)
            return error_response

    async def get_register_summary_data(self, get_register_summary_data_request: GetRegisterSummaryDataRequest) -> RegisterSummaryDataResponse:
        try:
            register_summary_data_list: list[RegisterSummaryData] = await self.g2p_register_controller_service.get_register_summary_data(get_register_summary_data_request)
            register_summary_data_response: RegisterSummaryDataResponse = self.helper.construct_register_summary_data_success_response(
                register_summary_data_list=register_summary_data_list, g2p_request=get_register_summary_data_request
            )
            return register_summary_data_response
        except Exception as error_exception:
            _logger.error(f"Error in get_register_summary_data: {str(error_exception)}")
            error_response: RegisterSummaryDataResponse = self.helper.construct_error_response(error_exception, get_register_summary_data_request)
            return error_response

    async def get_register_changelog_data(self, get_changelog_summary_data_request: GetChangeLogSummaryDataRequest) -> ChangeLogSummaryDataResponse:
        try:
            changelog_summary_data_list: list[ChangeLogSummaryData] = await self.g2p_register_controller_service.get_changelog_summary_data(get_changelog_summary_data_request)
            changelog_summary_data_response: ChangeLogSummaryDataResponse = self.helper.construct_changelog_summary_data_success_response(
                changelog_summary_data_list=changelog_summary_data_list, g2p_request=get_changelog_summary_data_request
            )
            return changelog_summary_data_response
        except Exception as error_exception:
            _logger.error(f"Error in get_register_changelog_data: {str(error_exception)}")
            error_response: ChangeLogSummaryDataResponse = self.helper.construct_error_response(error_exception, get_changelog_summary_data_request)
            return error_response

    async def get_all_registers(self, get_all_registers_request: GetAllRegistersRequest) -> AllRegistersResponse:
        try:
            all_registers_list: list[RegisterData] = await self.g2p_register_controller_service.get_all_registers(get_all_registers_request)
            all_registers_response: AllRegistersResponse = self.helper.construct_all_registers_success_response(
                all_registers_list=all_registers_list, g2p_request=get_all_registers_request
            )
            return all_registers_response
        except Exception as error_exception:
            _logger.error(f"Error in get_all_registers: {str(error_exception)}")
            error_response: AllRegistersResponse = self.helper.construct_error_response(error_exception, get_all_registers_request)
            return error_response

    async def get_child_registers(self, get_child_registers_request: GetChildRegistersRequest) -> ChildRegistersResponse:
        try:
            child_registers_list: list[ChildRegisterData] = await self.g2p_register_controller_service.get_child_registers(get_child_registers_request)
            child_registers_response: ChildRegistersResponse = self.helper.construct_child_registers_success_response(
                child_registers_list=child_registers_list, g2p_request=get_child_registers_request
            )
            return child_registers_response
        except Exception as error_exception:
            _logger.error(f"Error in get_child_registers: {str(error_exception)}")
            error_response: ChildRegistersResponse = self.helper.construct_error_response(error_exception, get_child_registers_request)
            return error_response

    async def search_in_a_register(self, search_register_request: SearchRegisterRequest) -> SearchResultsResponse:
        try:
            search_results_list, total_items, number_of_pages = await self.g2p_register_controller_service.search_in_a_register(search_register_request)
            search_results_response: SearchResultsResponse = self.helper.construct_search_results_success_response(
                search_results_list=search_results_list, g2p_request=search_register_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return search_results_response
        except Exception as error_exception:
            _logger.error(f"Error in search_in_a_register: {str(error_exception)}")
            error_response: SearchResultsResponse = self.helper.construct_error_response(error_exception, search_register_request)
            return error_response

    async def search_in_change_log(self, search_change_log_request: SearchChangeLogRequest) -> ChangeLogSearchResultsResponse:
        try:
            search_results_list, total_items, number_of_pages = await self.g2p_register_controller_service.search_in_change_log(search_change_log_request)
            search_results_response: ChangeLogSearchResultsResponse = self.helper.construct_change_log_search_results_success_response(
                search_results_list=search_results_list, g2p_request=search_change_log_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return search_results_response
        except Exception as error_exception:
            _logger.error(f"Error in search_in_change_log: {str(error_exception)}")
            error_response: ChangeLogSearchResultsResponse = self.helper.construct_error_response(error_exception, search_change_log_request)
            return error_response

    async def get_number_of_versions(self, get_number_of_versions_request: GetNumberOfVersionsRequest) -> NumberOfVersionsResponse:
        try:
            number_of_versions_data: NumberOfVersionsData = await self.g2p_register_controller_service.get_number_of_versions(get_number_of_versions_request)
            number_of_versions_response: NumberOfVersionsResponse = self.helper.construct_number_of_versions_success_response(
                number_of_versions_data=number_of_versions_data, g2p_request=get_number_of_versions_request
            )
            return number_of_versions_response
        except Exception as error_exception:
            _logger.error(f"Error in get_number_of_versions: {str(error_exception)}")
            error_response: NumberOfVersionsResponse = self.helper.construct_error_response(error_exception, get_number_of_versions_request)
            return error_response

    async def get_number_of_pending_change_logs(self, get_number_of_pending_change_logs_request: GetNumberOfPendingChangeLogsRequest) -> NumberOfPendingChangeLogsResponse:
        try:
            number_of_pending_change_logs_data: NumberOfPendingChangeLogsData = await self.g2p_register_controller_service.get_number_of_pending_change_logs(get_number_of_pending_change_logs_request)
            number_of_pending_change_logs_response: NumberOfPendingChangeLogsResponse = self.helper.construct_number_of_pending_change_logs_success_response(
                number_of_pending_change_logs_data=number_of_pending_change_logs_data, g2p_request=get_number_of_pending_change_logs_request
            )
            return number_of_pending_change_logs_response
        except Exception as error_exception:
            _logger.error(f"Error in get_number_of_pending_change_logs: {str(error_exception)}")
            error_response: NumberOfPendingChangeLogsResponse = self.helper.construct_error_response(error_exception, get_number_of_pending_change_logs_request)
            return error_response

    async def get_change_logs(self, get_change_logs_request: GetChangeLogsRequest) -> ChangeLogsDataResponse:
        try:
            change_logs_list, total_items, number_of_pages = await self.g2p_register_controller_service.get_change_logs(get_change_logs_request)
            change_logs_response: ChangeLogsDataResponse = self.helper.construct_change_logs_success_response(
                change_logs_list=change_logs_list, g2p_request=get_change_logs_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return change_logs_response
        except Exception as error_exception:
            _logger.error(f"Error in get_change_logs: {str(error_exception)}")
            error_response: ChangeLogsDataResponse = self.helper.construct_error_response(error_exception, get_change_logs_request)
            return error_response

    async def get_change_log(self, get_change_log_request: GetChangeLogRequest) -> ChangeLogDataResponse:
        try:
            change_log_data: ChangeLogData = await self.g2p_register_controller_service.get_change_log(get_change_log_request)
            change_log_response: ChangeLogDataResponse = self.helper.construct_change_log_data_success_response(
                change_log_data=change_log_data, g2p_request=get_change_log_request
            )
            return change_log_response
        except Exception as error_exception:
            _logger.error(f"Error in get_change_log: {str(error_exception)}")
            error_response: ChangeLogDataResponse = self.helper.construct_error_response(error_exception, get_change_log_request)
            return error_response

    async def get_record(self, get_record_request: GetRecordRequest) -> RecordDataResponse:
        try:
            record_data: RecordData = await self.g2p_register_controller_service.get_record(get_record_request)
            record_response: RecordDataResponse = self.helper.construct_record_success_response(
                record_data=record_data, g2p_request=get_record_request
            )
            return record_response
        except Exception as error_exception:
            _logger.error(f"Error in get_record: {str(error_exception)}")
            error_response: RecordDataResponse = self.helper.construct_error_response(error_exception, get_record_request)
            return error_response

    async def get_verifications_for_change_log(self, get_verifications_request: GetVerificationsRequest) -> VerificationsDataResponse:
        try:
            verifications_list, total_items, number_of_pages = await self.g2p_register_controller_service.get_verifications_for_change_log(get_verifications_request)
            verifications_response: VerificationsDataResponse = self.helper.construct_verifications_success_response(
                verifications_list=verifications_list, g2p_request=get_verifications_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return verifications_response
        except Exception as error_exception:
            _logger.error(f"Error in get_verifications_for_change_log: {str(error_exception)}")
            error_response: VerificationsDataResponse = self.helper.construct_error_response(error_exception, get_verifications_request)
            return error_response

    async def add_verification_for_change_log(self, add_verification_request: AddVerificationRequest) -> VerificationDataResponse:
        try:
            verification_data: VerificationData = await self.g2p_register_controller_service.add_verification_for_change_log(add_verification_request)
            verification_response: VerificationDataResponse = self.helper.construct_verification_success_response(
                verification_data=verification_data, g2p_request=add_verification_request
            )
            return verification_response
        except Exception as error_exception:
            _logger.error(f"Error in add_verification_for_change_log: {str(error_exception)}")
            error_response: VerificationDataResponse = self.helper.construct_error_response(error_exception, add_verification_request)
            return error_response

    async def get_deduplication_register_results(self, get_deduplication_register_results_request: GetDeduplicationRegisterResultsRequest) -> DeduplicationRegisterResultsDataResponse:
        """
        Get deduplication results for a change log against register records.
        """
        try:
            dedup_results_list, total_items, number_of_pages = await self.g2p_register_controller_service.get_deduplication_register_results(get_deduplication_register_results_request)
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
            dedup_results_list, total_items, number_of_pages = await self.g2p_register_controller_service.get_deduplication_changelog_results(get_deduplication_changelog_results_request)
            dedup_results_response: DeduplicationChangelogResultsDataResponse = self.helper.construct_deduplication_changelog_results_success_response(
                dedup_results_list=dedup_results_list, g2p_request=get_deduplication_changelog_results_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return dedup_results_response
        except Exception as error_exception:
            _logger.error(f"Error in get_deduplication_changelog_results: {str(error_exception)}")
            error_response: DeduplicationChangelogResultsDataResponse = self.helper.construct_error_response(error_exception, get_deduplication_changelog_results_request)
            return error_response

    async def get_register_schema(self, get_register_schema_request: GetRegisterSchemaRequest) -> RegisterSchemaDataResponse:
        """
        Get register schema configuration for a given register_id.
        """
        try:
            register_schema_data: RegisterSchemaData = await self.g2p_register_controller_service.get_register_schema(get_register_schema_request)
            register_schema_response: RegisterSchemaDataResponse = self.helper.construct_register_schema_success_response(
                register_schema_data=register_schema_data, g2p_request=get_register_schema_request
            )
            return register_schema_response
        except Exception as error_exception:
            _logger.error(f"Error in get_register_schema: {str(error_exception)}")
            error_response: RegisterSchemaDataResponse = self.helper.construct_error_response(error_exception, get_register_schema_request)
            return error_response

    async def get_register_sections(self, get_register_sections_request: GetRegisterSectionsRequest) -> RegisterSectionsDataResponse:
        """
        Get register sections for a given register_id.
        """
        try:
            register_sections_list: list[RegisterSectionData] = await self.g2p_register_controller_service.get_register_sections(get_register_sections_request)
            register_sections_response: RegisterSectionsDataResponse = self.helper.construct_register_sections_success_response(
                register_sections_list=register_sections_list, g2p_request=get_register_sections_request
            )
            return register_sections_response
        except Exception as error_exception:
            _logger.error(f"Error in get_register_sections: {str(error_exception)}")
            error_response: RegisterSectionsDataResponse = self.helper.construct_error_response(error_exception, get_register_sections_request)
            return error_response