from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
)
from .outgest_payload import (
    OutgoingTopicPayload,
    OutgoingTopicUpdatePayload,
    OutgoingTemplatePayload,
    OutgoingTemplateUpdatePayload,
)


# =============================================================================
# OutgoingTopic Request Schemas
# =============================================================================

class OutgoingTopicRequestBody(G2PRequestBody):
    request_payload: OutgoingTopicPayload


class OutgoingTopicRequest(G2PRequest):
    request_body: OutgoingTopicRequestBody


class OutgoingTopicUpdateRequestBody(G2PRequestBody):
    request_payload: OutgoingTopicUpdatePayload


class OutgoingTopicUpdateRequest(G2PRequest):
    request_body: OutgoingTopicUpdateRequestBody


# =============================================================================
# OutgoingTemplate Request Schemas
# =============================================================================

class OutgoingTemplateRequestBody(G2PRequestBody):
    request_payload: OutgoingTemplatePayload


class OutgoingTemplateRequest(G2PRequest):
    request_body: OutgoingTemplateRequestBody


class OutgoingTemplateUpdateRequestBody(G2PRequestBody):
    request_payload: OutgoingTemplateUpdatePayload


class OutgoingTemplateUpdateRequest(G2PRequest):
    request_body: OutgoingTemplateUpdateRequestBody
