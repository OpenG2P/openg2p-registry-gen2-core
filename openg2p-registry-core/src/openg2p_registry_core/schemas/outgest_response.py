from typing import Optional, List
from openg2p_fastapi_common.schemas import (
    G2PResponse,
    G2PResponseBody,
)
from .outgest_payload import (
    OutgoingTopicData,
    OutgoingTemplateData,
)


# =============================================================================
# OutgoingTopic Response Schemas
# =============================================================================

class OutgoingTopicResponseBody(G2PResponseBody):
    response_payload: Optional[List[OutgoingTopicData]] = None


class OutgoingTopicResponse(G2PResponse):
    response_body: Optional[OutgoingTopicResponseBody] = None


# =============================================================================
# OutgoingTemplate Response Schemas
# =============================================================================

class OutgoingTemplateResponseBody(G2PResponseBody):
    response_payload: Optional[List[OutgoingTemplateData]] = None


class OutgoingTemplateResponse(G2PResponse):
    response_body: Optional[OutgoingTemplateResponseBody] = None
