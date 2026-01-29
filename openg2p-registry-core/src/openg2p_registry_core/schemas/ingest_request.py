from fastapi import Request
from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
)
from .ingest_payload import (
    EmptyIngestionRequestPayload,
    GetIngestionDataRequestPayload,
    IncomingPartnerPayload,
    IncomingPartnerUpdatePayload,
    IncomingModelKeyPathPayload,
    IncomingModelKeyPathUpdatePayload,
    EditKeyPathForMessageIdPayload,
    EditKeyPathForSenderPayload,
    EditKeyPathForSignaturePayload,
    EditKeyPathForSignaturePayloadPayload,
    EditIsListPayload,
    EditKeyPathForListElementsPayload,
    DeleteIncomingKeyPathPayload,
    IncomingModelSemanticPatternPayload,
    IncomingModelSemanticPatternUpdatePayload,
    IncomingTemplatePayload,
    IncomingTemplateUpdatePayload,
    DataModelPayload,
    DataModelUpdatePayload,
    ChangeResponseTemplateFilePayload,
    ChangeActiveStatusPayload,
    SubscriptionActivityLogPayload,
    G2PInputMechanismPayload
)


# =============================================================================
# Ingest Data Request (base request for ingestion)
# =============================================================================

class IngestDataRequest(Request):
    # Request structure is internal to partners
    pass


# =============================================================================
# Ingestion Summary Requests
# =============================================================================

class GetIngestionSummaryDataRequestBody(G2PRequestBody):
    request_payload: EmptyIngestionRequestPayload


class GetIngestionSummaryDataRequest(G2PRequest):
    request_body: GetIngestionSummaryDataRequestBody


# =============================================================================
# Ingestion Search Requests
# =============================================================================

class SearchIngestionDataRequestBody(G2PRequestBody):
    request_payload: EmptyIngestionRequestPayload


class SearchIngestionDataRequest(G2PRequest):
    request_body: SearchIngestionDataRequestBody


# =============================================================================
# Ingestion Data Payload Requests
# =============================================================================

class GetIngestionDataPayloadRequestBody(G2PRequestBody):
    request_payload: GetIngestionDataRequestPayload


class GetIngestionDataPayloadRequest(G2PRequest):
    request_body: GetIngestionDataPayloadRequestBody


# =============================================================================
# IncomingPartner Request Schemas
# =============================================================================

class IncomingPartnerRequestBody(G2PRequestBody):
    request_payload: IncomingPartnerPayload


class IncomingPartnerRequest(G2PRequest):
    request_body: IncomingPartnerRequestBody


class IncomingPartnerUpdateRequestBody(G2PRequestBody):
    request_payload: IncomingPartnerUpdatePayload


class IncomingPartnerUpdateRequest(G2PRequest):
    request_body: IncomingPartnerUpdateRequestBody


# =============================================================================
# IncomingModelKeyPath Request Schemas
# =============================================================================

class IncomingModelKeyPathRequestBody(G2PRequestBody):
    request_payload: IncomingModelKeyPathPayload


class IncomingModelKeyPathRequest(G2PRequest):
    request_body: IncomingModelKeyPathRequestBody


class IncomingModelKeyPathUpdateRequestBody(G2PRequestBody):
    request_payload: IncomingModelKeyPathUpdatePayload


class IncomingModelKeyPathUpdateRequest(G2PRequest):
    request_body: IncomingModelKeyPathUpdateRequestBody


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


# =============================================================================
# IncomingModelSemanticPattern Request Schemas
# =============================================================================

class IncomingModelSemanticPatternRequestBody(G2PRequestBody):
    request_payload: IncomingModelSemanticPatternPayload


class IncomingModelSemanticPatternRequest(G2PRequest):
    request_body: IncomingModelSemanticPatternRequestBody


class IncomingModelSemanticPatternUpdateRequestBody(G2PRequestBody):
    request_payload: IncomingModelSemanticPatternUpdatePayload


class IncomingModelSemanticPatternUpdateRequest(G2PRequest):
    request_body: IncomingModelSemanticPatternUpdateRequestBody


# =============================================================================
# IncomingTemplate Request Schemas
# =============================================================================

class IncomingTemplateRequestBody(G2PRequestBody):
    request_payload: IncomingTemplatePayload


class IncomingTemplateRequest(G2PRequest):
    request_body: IncomingTemplateRequestBody


class IncomingTemplateUpdateRequestBody(G2PRequestBody):
    request_payload: IncomingTemplateUpdatePayload


class IncomingTemplateUpdateRequest(G2PRequest):
    request_body: IncomingTemplateUpdateRequestBody


# =============================================================================
# DataModel Request Schemas
# =============================================================================

class DataModelRequestBody(G2PRequestBody):
    request_payload: DataModelPayload


class DataModelRequest(G2PRequest):
    request_body: DataModelRequestBody


class DataModelUpdateRequestBody(G2PRequestBody):
    request_payload: DataModelUpdatePayload


class DataModelUpdateRequest(G2PRequest):
    request_body: DataModelUpdateRequestBody


class ChangeResponseTemplateFileRequestBody(G2PRequestBody):
    request_payload: ChangeResponseTemplateFilePayload


class ChangeResponseTemplateFileRequest(G2PRequest):
    request_body: ChangeResponseTemplateFileRequestBody


class ChangeActiveStatusRequestBody(G2PRequestBody):
    request_payload: ChangeActiveStatusPayload


class ChangeActiveStatusRequest(G2PRequest):
    request_body: ChangeActiveStatusRequestBody


# =============================================================================
# SubscriptionActivityLog Request Schemas
# =============================================================================

class SubscriptionActivityLogRequestBody(G2PRequestBody):
    request_payload: SubscriptionActivityLogPayload


class SubscriptionActivityLogRequest(G2PRequest):
    request_body: SubscriptionActivityLogRequestBody

# =============================================================================
# G2P Input Mechanism Request Schemas
# =============================================================================

class G2PInputMechanismRequestBody(G2PRequestBody):
    request_payload: G2PInputMechanismPayload


class G2PInputMechanismRequest(G2PRequest):
    request_body: G2PInputMechanismRequestBody
