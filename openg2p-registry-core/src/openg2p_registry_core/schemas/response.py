from typing import Optional, List

from openg2p_fastapi_common.schemas import (
    G2PResponse,
    G2PResponseBody,
)
from .payload import ChangeLogPayload, RegisterSummaryData

class ChangeLogResponseBody(G2PResponseBody):
    response_payload: Optional[ChangeLogPayload] = None

class ChangeLogResponse(G2PResponse):
    response_body: Optional[ChangeLogResponseBody] = None


class RegisterSummaryDataResponseBody(G2PResponseBody):
    response_payload: Optional[List[RegisterSummaryData]] = None

class RegisterSummaryDataResponse(G2PResponse):
    response_body: Optional[RegisterSummaryDataResponseBody] = None