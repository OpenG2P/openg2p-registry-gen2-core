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
    ChangeLogSearchResultsResponse, ChangeLogSearchResultData
)
from openg2p_registry_core.errors import G2PRegistryException
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


    async def create_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:
        #TODO: Validate Staff Token here with auth: Annotated[AuthCredentials, Depends(AuthFactory())]

        try:
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.create_change_log(change_log_request)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_payload=change_log_payload, g2p_request=change_log_request
            )
            return change_log_response
        except G2PRegistryException as gre:
            _logger.error(f"G2PRegistryException in create_change_log: {str(gre)}")
            error_response: G2PResponse = self.helper.construct_registry_error_response(gre, change_log_request)
            return error_response
        except Exception as e:
            _logger.error(f"Error in create_change_log: {str(e)}")
            error_response: G2PResponse = self.helper.construct_error_response(e, change_log_request)
            return error_response

    async def approve_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:

        try:
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.approve_change_log(change_log_request.request_body.request_payload.change_log_id)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_payload=change_log_payload, g2p_request=change_log_request
            )
            return change_log_response
        except G2PRegistryException as gre:
            _logger.error(f"G2PRegistryException in approve_change_log: {str(gre)}")
            error_response: G2PResponse = self.helper.construct_registry_error_response(gre, change_log_request)
            return error_response
        except Exception as e:
            _logger.error(f"Error in approve_change_log: {str(e)}")
            error_response: G2PResponse = self.helper.construct_error_response(e, change_log_request)
            return error_response
    
    async def reject_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:
        try:
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.reject_change_log(change_log_request.request_body.request_payload.change_log_id)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_payload=change_log_payload, g2p_request=change_log_request
            )
            return change_log_response
        except G2PRegistryException as gre:
            _logger.error(f"G2PRegistryException in reject_change_log: {str(gre)}")
            error_response: G2PResponse = self.helper.construct_registry_error_response(gre, change_log_request)
            return error_response
        except Exception as e:
            _logger.error(f"Error in reject_change_log: {str(e)}")
            error_response: G2PResponse = self.helper.construct_error_response(e, change_log_request)
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
            error_response: RegisterSummaryDataResponse = self.helper.construct_register_summary_data_error_response(error_exception)
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
            error_response: AllRegistersResponse = self.helper.construct_all_registers_error_response(error_exception)
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
            error_response: ChildRegistersResponse = self.helper.construct_child_registers_error_response(error_exception)
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
            error_response: SearchResultsResponse = self.helper.construct_search_results_error_response(error_exception)
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
            error_response: ChangeLogSearchResultsResponse = self.helper.construct_change_log_search_results_error_response(error_exception)
            return error_response