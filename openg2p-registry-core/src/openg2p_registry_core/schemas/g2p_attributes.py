from typing import Optional, List
from pydantic import BaseModel
from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PResponse,
    G2PResponseBody,
    G2PResponseHeader,
)


# Data Payloads
class G2PAttributeValueData(BaseModel):
    value_id: str
    attribute_id: str
    value_code: str
    value_display: str
    parent_value_id: Optional[str] = None
    sort_order: int


# Request Payloads
class GetG2PAttributeValuesRequestPayload(BaseModel):
    attribute_id: str
    parent_value_id: Optional[str] = None


class GetG2PAttributeValuesRequestBody(G2PRequestBody):
    request_payload: GetG2PAttributeValuesRequestPayload


class GetG2PAttributeValuesRequest(G2PRequest):
    request_body: GetG2PAttributeValuesRequestBody


# Response Payloads
class GetG2PAttributeValuesResponseBody(G2PResponseBody):
    response_payload: List[G2PAttributeValueData]


class GetG2PAttributeValuesResponse(G2PResponse):
    response_header: G2PResponseHeader
    response_body: GetG2PAttributeValuesResponseBody

