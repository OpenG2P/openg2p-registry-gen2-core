from datetime import datetime
from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.schemas import G2PRequest, G2PResponse, G2PResponseHeader, G2PResponseStatus, G2PResponseBody
from openg2p_registry_core.schemas import IngestDataPayload, IngestDataRequest, IngestDataResponse, IngestDataResponseBody
from openg2p_registry_core.errors import G2PRegistryException
from fastapi import Request

class RequestResponseHelper(BaseService):
    def construct_ingest_data_success_response(self, ingest_data_payload: IngestDataPayload, ingest_data_request: Request) -> IngestDataResponse:
        
        g2p_response_header = G2PResponseHeader(
            request_id=ingest_data_request.request_header.request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )
        
        response_body: IngestDataResponseBody = IngestDataResponseBody(
            response_payload=ingest_data_payload
        )

        ingest_data_response: IngestDataResponse = IngestDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return ingest_data_response
    
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
