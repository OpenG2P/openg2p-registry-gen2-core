from typing import Optional, List
from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PResponse,
    G2PResponseBody,
)
from .ingestion_configuration import (
    IncomingPartnerPayload,
    IncomingPartnerUpdatePayload,
    IncomingPartnerData,
    IncomingModelSignaturePatternPayload,
    IncomingModelSignaturePatternUpdatePayload,
    IncomingModelSignaturePatternData,
)


# IncomingPartner Request/Response
class IncomingPartnerRequestBody(G2PRequestBody):
    request_payload: IncomingPartnerPayload


class IncomingPartnerRequest(G2PRequest):
    request_body: IncomingPartnerRequestBody


class IncomingPartnerUpdateRequestBody(G2PRequestBody):
    request_payload: IncomingPartnerUpdatePayload


class IncomingPartnerUpdateRequest(G2PRequest):
    request_body: IncomingPartnerUpdateRequestBody


class IncomingPartnerResponseBody(G2PResponseBody):
    response_payload: Optional[IncomingPartnerData] = None


class IncomingPartnerResponse(G2PResponse):
    response_body: Optional[IncomingPartnerResponseBody] = None


class IncomingPartnersResponseBody(G2PResponseBody):
    response_payload: Optional[List[IncomingPartnerData]] = None


class IncomingPartnersResponse(G2PResponse):
    response_body: Optional[IncomingPartnersResponseBody] = None


# IncomingModelSignaturePattern Request/Response
class IncomingModelSignaturePatternRequestBody(G2PRequestBody):
    request_payload: IncomingModelSignaturePatternPayload


class IncomingModelSignaturePatternRequest(G2PRequest):
    request_body: IncomingModelSignaturePatternRequestBody


class IncomingModelSignaturePatternUpdateRequestBody(G2PRequestBody):
    request_payload: IncomingModelSignaturePatternUpdatePayload


class IncomingModelSignaturePatternUpdateRequest(G2PRequest):
    request_body: IncomingModelSignaturePatternUpdateRequestBody


class IncomingModelSignaturePatternResponseBody(G2PResponseBody):
    response_payload: Optional[IncomingModelSignaturePatternData] = None


class IncomingModelSignaturePatternResponse(G2PResponse):
    response_body: Optional[IncomingModelSignaturePatternResponseBody] = None


class IncomingModelSignaturePatternsResponseBody(G2PResponseBody):
    response_payload: Optional[List[IncomingModelSignaturePatternData]] = None


class IncomingModelSignaturePatternsResponse(G2PResponse):
    response_body: Optional[IncomingModelSignaturePatternsResponseBody] = None

