from typing import Optional, List
from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PResponse,
    G2PResponseBody,
)
from .outgestion_configuration import (
    OutgoingTopicPayload,
    OutgoingTopicUpdatePayload,
    OutgoingTopicData,
    OutgoingTemplatePayload,
    OutgoingTemplateUpdatePayload,
    OutgoingTemplateData,
)


# OutgoingTopic Request/Response
class OutgoingTopicRequestBody(G2PRequestBody):
    request_payload: OutgoingTopicPayload


class OutgoingTopicRequest(G2PRequest):
    request_body: OutgoingTopicRequestBody


class OutgoingTopicUpdateRequestBody(G2PRequestBody):
    request_payload: OutgoingTopicUpdatePayload


class OutgoingTopicUpdateRequest(G2PRequest):
    request_body: OutgoingTopicUpdateRequestBody


class OutgoingTopicResponseBody(G2PResponseBody):
    response_payload: Optional[List[OutgoingTopicData]] = None


class OutgoingTopicResponse(G2PResponse):
    response_body: Optional[OutgoingTopicResponseBody] = None

# OutgoingTemplate Request/Response
class OutgoingTemplateRequestBody(G2PRequestBody):
    request_payload: OutgoingTemplatePayload


class OutgoingTemplateRequest(G2PRequest):
    request_body: OutgoingTemplateRequestBody


class OutgoingTemplateUpdateRequestBody(G2PRequestBody):
    request_payload: OutgoingTemplateUpdatePayload


class OutgoingTemplateUpdateRequest(G2PRequest):
    request_body: OutgoingTemplateUpdateRequestBody


class OutgoingTemplateResponseBody(G2PResponseBody):
    response_payload: Optional[List[OutgoingTemplateData]] = None


class OutgoingTemplateResponse(G2PResponse):
    response_body: Optional[OutgoingTemplateResponseBody] = None
