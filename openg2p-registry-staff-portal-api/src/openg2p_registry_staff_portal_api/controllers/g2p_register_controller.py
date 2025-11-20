import logging
from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PRegisterControllerService
from openg2p_registry_core.schemas import (
    ChangeLogRequest, ChangeLogResponse, ChangeLogPayload,
    RegisterSummaryDataResponse, RegisterSummaryData,
    AllRegistersResponse, RegisterData,
    ChildRegistersResponse, ChildRegisterData,
    ChildRegisterRequest,
    SearchResultsResponse, SearchResultData,
    ChangeLogSearchResultsResponse, ChangeLogSearchResultData,
    NumberOfVersionsResponse, NumberOfVersionsData,
    ChangeLogDataResponse, ChangeLogData,
    ChangeLogsDataResponse, ChangeLogsData,
    RecordDataResponse, RecordData,
    VerificationsDataResponse, VerificationsData
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
            methods=["GET"],
        )

        self.router.add_api_route(
            "/get_all_registers",
            self.get_all_registers,
            responses={200: {"model": AllRegistersResponse}},
            methods=["GET"],
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
            methods=["GET"],
        )

        self.router.add_api_route(
            "/get_change_logs",
            self.get_change_logs,
            responses={200: {"model": ChangeLogsDataResponse}},
            methods=["GET"],
        )

        self.router.add_api_route(
            "/get_change_log",
            self.get_change_log,
            responses={200: {"model": ChangeLogDataResponse}},
            methods=["GET"],
        )

        self.router.add_api_route(
            "/get_record",
            self.get_record,
            responses={200: {"model": RecordDataResponse}},
            methods=["GET"],
        )

        self.router.add_api_route(
            "/get_verifications_for_change_log",
            self.get_verifications_for_change_log,
            responses={200: {"model": VerificationsDataResponse}},
            methods=["GET"],
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
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.approve_change_log(change_log_request.request_body.request_payload.change_log_id)
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
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.reject_change_log(change_log_request.request_body.request_payload.change_log_id)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_payload=change_log_payload, g2p_request=change_log_request
            )
            return change_log_response
        except Exception as error_exception:
            _logger.error(f"Error in reject_change_log: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, change_log_request)
            return error_response

    async def get_register_summary_data(self) -> RegisterSummaryDataResponse:
        try:
            register_summary_data_list: list[RegisterSummaryData] = await self.g2p_register_controller_service.get_register_summary_data()
            register_summary_data_response: RegisterSummaryDataResponse = self.helper.construct_register_summary_data_success_response(
                register_summary_data_list=register_summary_data_list
            )
            return register_summary_data_response
        except Exception as error_exception:
            _logger.error(f"Error in get_register_summary_data: {str(error_exception)}")
            error_response: RegisterSummaryDataResponse = self.helper.construct_error_response(error_exception)
            return error_response

    async def get_all_registers(self) -> AllRegistersResponse:
        try:
            all_registers_list: list[RegisterData] = await self.g2p_register_controller_service.get_all_registers()
            all_registers_response: AllRegistersResponse = self.helper.construct_all_registers_success_response(
                all_registers_list=all_registers_list
            )
            return all_registers_response
        except Exception as error_exception:
            _logger.error(f"Error in get_all_registers: {str(error_exception)}")
            error_response: AllRegistersResponse = self.helper.construct_error_response(error_exception)
            return error_response

    async def get_child_registers(self, register_id: str) -> ChildRegistersResponse:
        try:
            child_registers_list: list[ChildRegisterData] = await self.g2p_register_controller_service.get_child_registers(register_id)
            child_registers_response: ChildRegistersResponse = self.helper.construct_child_registers_success_response(
                child_registers_list=child_registers_list
            )
            return child_registers_response
        except Exception as error_exception:
            _logger.error(f"Error in get_child_registers: {str(error_exception)}")
            error_response: ChildRegistersResponse = self.helper.construct_error_response(error_exception)
            return error_response

    async def search_in_a_register(self, register_id: str, search_text: str) -> SearchResultsResponse:
        try:
            search_results_list: list[SearchResultData] = await self.g2p_register_controller_service.search_in_a_register(register_id, search_text)
            search_results_response: SearchResultsResponse = self.helper.construct_search_results_success_response(
                search_results_list=search_results_list
            )
            return search_results_response
        except Exception as error_exception:
            _logger.error(f"Error in search_in_a_register: {str(error_exception)}")
            error_response: SearchResultsResponse = self.helper.construct_error_response(error_exception)
            return error_response

    async def search_in_change_log(self, search_text: str) -> ChangeLogSearchResultsResponse:
        try:
            search_results_list: list[ChangeLogSearchResultData] = await self.g2p_register_controller_service.search_in_change_log(search_text)
            search_results_response: ChangeLogSearchResultsResponse = self.helper.construct_change_log_search_results_success_response(
                search_results_list=search_results_list
            )
            return search_results_response
        except Exception as error_exception:
            _logger.error(f"Error in search_in_change_log: {str(error_exception)}")
            error_response: ChangeLogSearchResultsResponse = self.helper.construct_error_response(error_exception)
            return error_response

    async def get_number_of_versions(self, register_id: str, internal_record_id: str) -> NumberOfVersionsResponse:
        try:
            number_of_versions_data: NumberOfVersionsData = await self.g2p_register_controller_service.get_number_of_versions(register_id, internal_record_id)
            number_of_versions_response: NumberOfVersionsResponse = self.helper.construct_number_of_versions_success_response(
                number_of_versions_data=number_of_versions_data
            )
            return number_of_versions_response
        except Exception as error_exception:
            _logger.error(f"Error in get_number_of_versions: {str(error_exception)}")
            error_response: NumberOfVersionsResponse = self.helper.construct_error_response(error_exception)
            return error_response

    async def get_change_logs(self, register_id: str, internal_record_id: str) -> ChangeLogsDataResponse:
        try:
            change_logs_data: ChangeLogsData = await self.g2p_register_controller_service.get_change_logs(register_id, internal_record_id)
            change_logs_response: ChangeLogsDataResponse = self.helper.construct_change_logs_success_response(
                change_logs_data=change_logs_data
            )
            return change_logs_response
        except Exception as error_exception:
            _logger.error(f"Error in get_change_logs: {str(error_exception)}")
            error_response: ChangeLogsDataResponse = self.helper.construct_error_response(error_exception)
            return error_response

    async def get_change_log(self, change_log_id: str) -> ChangeLogDataResponse:
        try:
            change_log_data: ChangeLogData = await self.g2p_register_controller_service.get_change_log(change_log_id)
            change_log_response: ChangeLogDataResponse = self.helper.construct_change_log_success_response(
                change_log_data=change_log_data
            )
            return change_log_response
        except Exception as error_exception:
            _logger.error(f"Error in get_change_log: {str(error_exception)}")
            error_response: ChangeLogDataResponse = self.helper.construct_error_response(error_exception)
            return error_response

    async def get_record(self, register_id: str, internal_record_id: str) -> RecordDataResponse:
        try:
            record_data: RecordData = await self.g2p_register_controller_service.get_record(register_id, internal_record_id)
            record_response: RecordDataResponse = self.helper.construct_record_success_response(
                record_data=record_data
            )
            return record_response
        except Exception as error_exception:
            _logger.error(f"Error in get_record: {str(error_exception)}")
            error_response: RecordDataResponse = self.helper.construct_error_response(error_exception)
            return error_response

    async def get_verifications_for_change_log(self, change_log_id: str) -> VerificationsDataResponse:
        try:
            verifications_data: VerificationsData = await self.g2p_register_controller_service.get_verifications_for_change_log(change_log_id)
            verifications_response: VerificationsDataResponse = self.helper.construct_verifications_success_response(
                verifications_data=verifications_data
            )
            return verifications_response
        except Exception as error_exception:
            _logger.error(f"Error in get_verifications_for_change_log: {str(error_exception)}")
            error_response: VerificationsDataResponse = self.helper.construct_error_response(error_exception)
            return error_response