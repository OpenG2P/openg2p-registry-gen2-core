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
    IncomingModelSemanticPatternPayload,
    IncomingModelSemanticPatternUpdatePayload,
    IncomingModelSemanticPatternData,
    IncomingTemplatePayload,
    IncomingTemplateUpdatePayload,
    IncomingTemplateData,
    IncomingPayloadEnricherPayload,
    IncomingPayloadEnricherUpdatePayload,
    IncomingPayloadEnricherData,
    DataModelPayload,
    DataModelUpdatePayload,
    DataModelData,
    SubscriptionActivityLogPayload,
    SubscriptionActivityLogData,
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


# IncomingModelSemanticPattern Request/Response
class IncomingModelSemanticPatternRequestBody(G2PRequestBody):
    request_payload: IncomingModelSemanticPatternPayload


class IncomingModelSemanticPatternRequest(G2PRequest):
    request_body: IncomingModelSemanticPatternRequestBody


class IncomingModelSemanticPatternUpdateRequestBody(G2PRequestBody):
    request_payload: IncomingModelSemanticPatternUpdatePayload


class IncomingModelSemanticPatternUpdateRequest(G2PRequest):
    request_body: IncomingModelSemanticPatternUpdateRequestBody


class IncomingModelSemanticPatternResponseBody(G2PResponseBody):
    response_payload: Optional[IncomingModelSemanticPatternData] = None


class IncomingModelSemanticPatternResponse(G2PResponse):
    response_body: Optional[IncomingModelSemanticPatternResponseBody] = None


class IncomingModelSemanticPatternsResponseBody(G2PResponseBody):
    response_payload: Optional[List[IncomingModelSemanticPatternData]] = None


class IncomingModelSemanticPatternsResponse(G2PResponse):
    response_body: Optional[IncomingModelSemanticPatternsResponseBody] = None


# IncomingTemplate Request/Response
class IncomingTemplateRequestBody(G2PRequestBody):
    request_payload: IncomingTemplatePayload


class IncomingTemplateRequest(G2PRequest):
    request_body: IncomingTemplateRequestBody


class IncomingTemplateUpdateRequestBody(G2PRequestBody):
    request_payload: IncomingTemplateUpdatePayload


class IncomingTemplateUpdateRequest(G2PRequest):
    request_body: IncomingTemplateUpdateRequestBody


class IncomingTemplateResponseBody(G2PResponseBody):
    response_payload: Optional[IncomingTemplateData] = None


class IncomingTemplateResponse(G2PResponse):
    response_body: Optional[IncomingTemplateResponseBody] = None


class IncomingTemplatesResponseBody(G2PResponseBody):
    response_payload: Optional[List[IncomingTemplateData]] = None


class IncomingTemplatesResponse(G2PResponse):
    response_body: Optional[IncomingTemplatesResponseBody] = None


# IncomingPayloadEnricher Request/Response
class IncomingPayloadEnricherRequestBody(G2PRequestBody):
    request_payload: IncomingPayloadEnricherPayload


class IncomingPayloadEnricherRequest(G2PRequest):
    request_body: IncomingPayloadEnricherRequestBody


class IncomingPayloadEnricherUpdateRequestBody(G2PRequestBody):
    request_payload: IncomingPayloadEnricherUpdatePayload


class IncomingPayloadEnricherUpdateRequest(G2PRequest):
    request_body: IncomingPayloadEnricherUpdateRequestBody


class IncomingPayloadEnricherResponseBody(G2PResponseBody):
    response_payload: Optional[IncomingPayloadEnricherData] = None


class IncomingPayloadEnricherResponse(G2PResponse):
    response_body: Optional[IncomingPayloadEnricherResponseBody] = None


class IncomingPayloadEnrichersResponseBody(G2PResponseBody):
    response_payload: Optional[List[IncomingPayloadEnricherData]] = None


class IncomingPayloadEnrichersResponse(G2PResponse):
    response_body: Optional[IncomingPayloadEnrichersResponseBody] = None


# DataModel Request/Response
class DataModelRequestBody(G2PRequestBody):
    request_payload: DataModelPayload


class DataModelRequest(G2PRequest):
    request_body: DataModelRequestBody


class DataModelUpdateRequestBody(G2PRequestBody):
    request_payload: DataModelUpdatePayload


class DataModelUpdateRequest(G2PRequest):
    request_body: DataModelUpdateRequestBody


class DataModelResponseBody(G2PResponseBody):
    response_payload: Optional[DataModelData] = None


class DataModelResponse(G2PResponse):
    response_body: Optional[DataModelResponseBody] = None


class DataModelsResponseBody(G2PResponseBody):
    response_payload: Optional[List[DataModelData]] = None


class DataModelsResponse(G2PResponse):
    response_body: Optional[DataModelsResponseBody] = None


# SubscriptionActivityLog Request/Response
class SubscriptionActivityLogRequestBody(G2PRequestBody):
    request_payload: SubscriptionActivityLogPayload


class SubscriptionActivityLogRequest(G2PRequest):
    request_body: SubscriptionActivityLogRequestBody


class SubscriptionActivityLogResponseBody(G2PResponseBody):
    response_payload: Optional[SubscriptionActivityLogData] = None


class SubscriptionActivityLogResponse(G2PResponse):
    response_body: Optional[SubscriptionActivityLogResponseBody] = None


class SubscriptionActivityLogsResponseBody(G2PResponseBody):
    response_payload: Optional[List[SubscriptionActivityLogData]] = None


class SubscriptionActivityLogsResponse(G2PResponse):
    response_body: Optional[SubscriptionActivityLogsResponseBody] = None

