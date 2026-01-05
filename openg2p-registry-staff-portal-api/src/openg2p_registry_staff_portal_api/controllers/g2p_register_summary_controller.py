import logging
from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PRegisterSummaryControllerService
from openg2p_registry_core.schemas import (
    RegisterSummaryDataResponse, RegisterSummaryData,
    GetRegisterSummaryDataRequest,
    SearchResultsResponse,
    SearchRegisterRequest,
    SearchChangeRequestRequest,
    ChangeRequestSearchResultsResponse
)

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PRegisterSummaryController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["G2P Register Summary"]
        self.g2p_register_summary_controller_service = G2PRegisterSummaryControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/register"

        self.router.add_api_route(
            "/get_register_summary_data",
            self.get_register_summary_data,
            responses={200: {"model": RegisterSummaryDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/search_in_a_register",
            self.search_in_a_register,
            responses={200: {"model": SearchResultsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/search_in_change_request",
            self.search_in_change_request,
            responses={200: {"model": ChangeRequestSearchResultsResponse}},
            methods=["POST"],
        )

    async def get_register_summary_data(self, get_register_summary_data_request: GetRegisterSummaryDataRequest) -> RegisterSummaryDataResponse:
        try:
            register_summary_data_list: list[RegisterSummaryData] = await self.g2p_register_summary_controller_service.get_register_summary_data(get_register_summary_data_request)
            register_summary_data_response: RegisterSummaryDataResponse = self.helper.construct_register_summary_data_success_response(
                register_summary_data_list=register_summary_data_list, g2p_request=get_register_summary_data_request
            )
            return register_summary_data_response
        except Exception as error_exception:
            _logger.error(f"Error in get_register_summary_data: {str(error_exception)}")
            error_response: RegisterSummaryDataResponse = self.helper.construct_error_response(error_exception, get_register_summary_data_request)
            return error_response

    async def search_in_a_register(self, search_register_request: SearchRegisterRequest) -> SearchResultsResponse:
        try:
            search_results_list, total_items, number_of_pages = await self.g2p_register_summary_controller_service.search_in_a_register(search_register_request)
            search_results_response: SearchResultsResponse = self.helper.construct_search_results_success_response(
                search_results_list=search_results_list, g2p_request=search_register_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return search_results_response
        except Exception as error_exception:
            _logger.error(f"Error in search_in_a_register: {str(error_exception)}")
            error_response: SearchResultsResponse = self.helper.construct_error_response(error_exception, search_register_request)
            return error_response

    async def search_in_change_request(self, search_change_request_request: SearchChangeRequestRequest) -> ChangeRequestSearchResultsResponse:
        try:
            search_results_list, total_items, number_of_pages = await self.g2p_register_summary_controller_service.search_in_change_request(search_change_request_request)
            search_results_response: ChangeRequestSearchResultsResponse = self.helper.construct_change_request_search_results_success_response(
                search_results_list=search_results_list, g2p_request=search_change_request_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return search_results_response
        except Exception as error_exception:
            _logger.error(f"Error in search_in_change_request: {str(error_exception)}")
            error_response: ChangeRequestSearchResultsResponse = self.helper.construct_error_response(error_exception, search_change_request_request)
            return error_response
