import logging
from openg2p_fastapi_common.service import BaseService

from ..services import G2PRegisterService
from ..schemas import (
    RegisterSummaryData,
    GetRegisterSummaryDataRequest,
    SearchRegisterRequest, SearchChangeRequestRequest,
    SearchResultData, ChangeRequestSearchResultData
)

_logger = logging.getLogger('g2p-register-summary-controller-service')


class G2PRegisterSummaryControllerService(BaseService):

    async def get_register_summary_data(self, get_register_summary_data_request: GetRegisterSummaryDataRequest) -> list[RegisterSummaryData]:
        _logger.info("Fetching register summary data through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        register_summary_data_list: list[RegisterSummaryData] = await g2p_register_service.get_register_summary_data()
        return register_summary_data_list

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

    async def search_in_change_request(self, search_change_request_request: SearchChangeRequestRequest) -> tuple[list[ChangeRequestSearchResultData], int, int]:
        pagination = search_change_request_request.request_body.pagination_request
        _logger.info(f"Searching in change requests with search_text: {pagination.search_text} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        search_results_list, total_items = await g2p_register_service.search_in_change_request(
            pagination.search_text, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return search_results_list, total_items, number_of_pages

