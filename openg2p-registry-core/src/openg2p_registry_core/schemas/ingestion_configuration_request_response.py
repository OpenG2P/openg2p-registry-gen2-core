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
    IncomingModelKeyPathPayload,
    IncomingModelKeyPathUpdatePayload,
    IncomingModelKeyPathData,
    IncomingModelKeyPathListData,
    EditKeyPathForMessageIdPayload,
    EditKeyPathForSenderPayload,
    EditKeyPathForSignaturePayload,
    EditKeyPathForSignaturePayloadPayload,
    EditIsListPayload,
    EditKeyPathForListElementsPayload,
    DeleteIncomingKeyPathPayload,
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


# IncomingModelKeyPath Request/Response
class IncomingModelKeyPathRequestBody(G2PRequestBody):
    request_payload: IncomingModelKeyPathPayload


class IncomingModelKeyPathRequest(G2PRequest):
    request_body: IncomingModelKeyPathRequestBody


class IncomingModelKeyPathUpdateRequestBody(G2PRequestBody):
    request_payload: IncomingModelKeyPathUpdatePayload


class IncomingModelKeyPathUpdateRequest(G2PRequest):
    request_body: IncomingModelKeyPathUpdateRequestBody


class IncomingModelKeyPathResponseBody(G2PResponseBody):
    response_payload: Optional[IncomingModelKeyPathData] = None


class IncomingModelKeyPathResponse(G2PResponse):
    response_body: Optional[IncomingModelKeyPathResponseBody] = None


class IncomingModelKeyPathsResponseBody(G2PResponseBody):
    response_payload: Optional[List[IncomingModelKeyPathData]] = None


class IncomingModelKeyPathsResponse(G2PResponse):
    response_body: Optional[IncomingModelKeyPathsResponseBody] = None


# List response for IncomingModelKeyPath with data_model_mnemonic
class IncomingModelKeyPathListResponseBody(G2PResponseBody):
    response_payload: Optional[List[IncomingModelKeyPathListData]] = None


class IncomingModelKeyPathListResponse(G2PResponse):
    response_body: Optional[IncomingModelKeyPathListResponseBody] = None


# Individual edit requests for IncomingModelKeyPath
class EditKeyPathForMessageIdRequestBody(G2PRequestBody):
    request_payload: EditKeyPathForMessageIdPayload


class EditKeyPathForMessageIdRequest(G2PRequest):
    request_body: EditKeyPathForMessageIdRequestBody


class EditKeyPathForSenderRequestBody(G2PRequestBody):
    request_payload: EditKeyPathForSenderPayload


class EditKeyPathForSenderRequest(G2PRequest):
    request_body: EditKeyPathForSenderRequestBody


class EditKeyPathForSignatureRequestBody(G2PRequestBody):
    request_payload: EditKeyPathForSignaturePayload


class EditKeyPathForSignatureRequest(G2PRequest):
    request_body: EditKeyPathForSignatureRequestBody


class EditKeyPathForSignaturePayloadRequestBody(G2PRequestBody):
    request_payload: EditKeyPathForSignaturePayloadPayload


class EditKeyPathForSignaturePayloadRequest(G2PRequest):
    request_body: EditKeyPathForSignaturePayloadRequestBody


class EditIsListRequestBody(G2PRequestBody):
    request_payload: EditIsListPayload


class EditIsListRequest(G2PRequest):
    request_body: EditIsListRequestBody


class EditKeyPathForListElementsRequestBody(G2PRequestBody):
    request_payload: EditKeyPathForListElementsPayload


class EditKeyPathForListElementsRequest(G2PRequest):
    request_body: EditKeyPathForListElementsRequestBody


class DeleteIncomingKeyPathRequestBody(G2PRequestBody):
    request_payload: DeleteIncomingKeyPathPayload


class DeleteIncomingKeyPathRequest(G2PRequest):
    request_body: DeleteIncomingKeyPathRequestBody


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

