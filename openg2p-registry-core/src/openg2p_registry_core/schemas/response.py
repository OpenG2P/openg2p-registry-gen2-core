from typing import Optional

from openg2p_fastapi_common.schemas import (
    G2PResponse,
    G2PResponseBody,
)
from .payload import ChangeLogPayload

class ChangeLogResponseBody(G2PResponseBody):
    response_payload: Optional[ChangeLogPayload] = None

class ChangeLogResponse(G2PResponse):
    response_body: Optional[ChangeLogResponseBody] = None