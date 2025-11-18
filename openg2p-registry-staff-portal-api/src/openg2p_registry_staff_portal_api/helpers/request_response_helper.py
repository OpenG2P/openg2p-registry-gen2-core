from datetime import datetime
from typing import List
from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.schemas import G2PRequest, G2PResponse, G2PResponseHeader, G2PResponseStatus, G2PResponseBody
from openg2p_registry_core.schemas import ChangeLogPayload, ChangeLogResponse, ChangeLogResponseBody, RegisterSummaryData, RegisterSummaryDataResponse, RegisterSummaryDataResponseBody
from openg2p_registry_core.errors import G2PRegistryException


class RequestResponseHelper(BaseService):
    def construct_change_log_success_response(self, change_log_payload: ChangeLogPayload, g2p_request: G2PRequest) -> ChangeLogResponse:

        g2p_response_header = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )
        
        response_body: ChangeLogResponseBody = ChangeLogResponseBody(
            response_payload=change_log_payload
        )

        change_log_response: ChangeLogResponse = ChangeLogResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return change_log_response
    
    def construct_registry_error_response(self, registry_exception: G2PRegistryException, g2p_request: G2PRequest) -> G2PResponse:

        g2p_response_header = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id,
            response_status=G2PResponseStatus.ERROR,
            response_error_code=registry_exception.code,
            response_error_message=registry_exception.message,
            response_timestamp=datetime.now()
        )
        error_response = G2PResponse(
            response_header=g2p_response_header,
            response_body=G2PResponseBody(
                pagination_response=None,
                response_payload=None
            )
        )

        return error_response

    def construct_error_response(self, error: Exception, g2p_request: G2PRequest) -> G2PResponse:

        g2p_response_header = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id,
            response_status=G2PResponseStatus.ERROR,
            response_error_code="500",
            response_error_message=str(error),
            response_timestamp=datetime.now()
        )
        error_response = G2PResponse(
            response_header=g2p_response_header,
            response_body=G2PResponseBody(
                pagination_response=None,
                response_payload=None
            )

        )

        return error_response

    def construct_register_summary_data_success_response(self, register_summary_data_list: List[RegisterSummaryData]) -> RegisterSummaryDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RegisterSummaryDataResponseBody = RegisterSummaryDataResponseBody(
            response_payload=register_summary_data_list
        )

        register_summary_data_response: RegisterSummaryDataResponse = RegisterSummaryDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return register_summary_data_response

    def construct_register_summary_data_error_response(self, error_exception: Exception) -> RegisterSummaryDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.ERROR,
            response_error_code="500",
            response_error_message=str(error_exception),
            response_timestamp=datetime.now()
        )

        response_body: RegisterSummaryDataResponseBody = RegisterSummaryDataResponseBody(
            response_payload=None
        )

        error_response: RegisterSummaryDataResponse = RegisterSummaryDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return error_response
