from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody
)
from .payload import ChangeLogPayload

class ChangeLogRequestBody(G2PRequestBody):
        request_payload: ChangeLogPayload

class ChangeLogRequest(G2PRequest):
    request_body: ChangeLogRequestBody