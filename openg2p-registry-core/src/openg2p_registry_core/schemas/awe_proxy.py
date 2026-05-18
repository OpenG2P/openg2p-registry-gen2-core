from typing import Any, List, Optional

from openg2p_fastapi_common.schemas import G2PRequest, G2PRequestBody, G2PResponse, G2PResponseBody
from pydantic import BaseModel, Field


class ListMyOpenAweTasksRequestPayload(BaseModel):
    request_id: Optional[str] = None
    artifact_type: Optional[str] = None
    policy_key: Optional[str] = None
    page: int = 1
    page_size: int = 25


class SubmitAweTaskDecisionRequestPayload(BaseModel):
    task_id: str
    action: str = Field(description="approve, reject, or abstain")
    comment: Optional[str] = None
    attachments_ref: Optional[str] = None


class ClaimAweTaskRequestPayload(BaseModel):
    task_id: str


class GetAweRequestRequestPayload(BaseModel):
    request_id: str


class GetAweRequestEventsRequestPayload(BaseModel):
    request_id: str


class AweProxyDataResponsePayload(BaseModel):
    data: Any


class ListMyOpenAweTasksRequestBody(G2PRequestBody):
    request_payload: ListMyOpenAweTasksRequestPayload


class ListMyOpenAweTasksRequest(G2PRequest):
    request_body: ListMyOpenAweTasksRequestBody


class SubmitAweTaskDecisionRequestBody(G2PRequestBody):
    request_payload: SubmitAweTaskDecisionRequestPayload


class SubmitAweTaskDecisionRequest(G2PRequest):
    request_body: SubmitAweTaskDecisionRequestBody


class ClaimAweTaskRequestBody(G2PRequestBody):
    request_payload: ClaimAweTaskRequestPayload


class ClaimAweTaskRequest(G2PRequest):
    request_body: ClaimAweTaskRequestBody


class GetAweRequestRequestBody(G2PRequestBody):
    request_payload: GetAweRequestRequestPayload


class GetAweRequestRequest(G2PRequest):
    request_body: GetAweRequestRequestBody


class GetAweRequestEventsRequestBody(G2PRequestBody):
    request_payload: GetAweRequestEventsRequestPayload


class GetAweRequestEventsRequest(G2PRequest):
    request_body: GetAweRequestEventsRequestBody


class AweProxyDataResponseBody(G2PResponseBody):
    response_payload: Optional[AweProxyDataResponsePayload] = None


class AweProxyDataResponse(G2PResponse):
    response_body: Optional[AweProxyDataResponseBody] = None


class AweProxyListDataResponseBody(G2PResponseBody):
    response_payload: Optional[List[Any]] = None


class AweProxyListDataResponse(G2PResponse):
    response_body: Optional[AweProxyListDataResponseBody] = None
