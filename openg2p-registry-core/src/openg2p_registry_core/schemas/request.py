from typing import Optional
from pydantic import BaseModel
from fastapi import Request
from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody
)
from .payload import ChangeRequestRequestPayload, AddVerificationPayload

class ChangeRequestRequestBody(G2PRequestBody):
    request_payload: ChangeRequestRequestPayload

class ChangeRequestRequest(G2PRequest):
    request_body: ChangeRequestRequestBody


class EmptyRequestPayload(BaseModel):
    """Empty payload for requests that don't require any parameters"""
    pass


class EmptyRequestBody(G2PRequestBody):
    request_payload: EmptyRequestPayload


class EmptyRequest(G2PRequest):
    request_body: EmptyRequestBody


class GetRegisterSummaryDataRequestBody(G2PRequestBody):
    request_payload: EmptyRequestPayload

class GetRegisterSummaryDataRequest(G2PRequest):
    request_body: GetRegisterSummaryDataRequestBody


class GetChangeRequestSummaryDataRequestBody(G2PRequestBody):
    request_payload: EmptyRequestPayload

class GetChangeRequestSummaryDataRequest(G2PRequest):
    request_body: GetChangeRequestSummaryDataRequestBody


class GetAllRegistersRequestBody(G2PRequestBody):
    request_payload: EmptyRequestPayload


class GetAllRegistersRequest(G2PRequest):
    request_body: GetAllRegistersRequestBody


class ChildRegisterRequestPayload(BaseModel):
    register_id: str


class ChildRegisterRequestBody(G2PRequestBody):
    request_payload: ChildRegisterRequestPayload

class ChildRegisterRequest(G2PRequest):
    request_body: ChildRegisterRequestBody


class SearchRegisterRequestPayload(BaseModel):
    register_id: str


class SearchRegisterRequestBody(G2PRequestBody):
    request_payload: SearchRegisterRequestPayload


class SearchRegisterRequest(G2PRequest):
    request_body: SearchRegisterRequestBody


class SearchChangeRequestRequestPayload(BaseModel):
    pass


class SearchChangeRequestRequestBody(G2PRequestBody):
    request_payload: SearchChangeRequestRequestPayload


class SearchChangeRequestRequest(G2PRequest):
    request_body: SearchChangeRequestRequestBody


class GetChildRegistersRequestPayload(BaseModel):
    register_id: str


class GetChildRegistersRequestBody(G2PRequestBody):
    request_payload: GetChildRegistersRequestPayload


class GetChildRegistersRequest(G2PRequest):
    request_body: GetChildRegistersRequestBody


class GetMasterRegisterRequestPayload(BaseModel):
    register_id: str


class GetMasterRegisterRequestBody(G2PRequestBody):
    request_payload: GetMasterRegisterRequestPayload


class GetMasterRegisterRequest(G2PRequest):
    request_body: GetMasterRegisterRequestBody


class GetNumberOfVersionsRequestPayload(BaseModel):
    register_id: str
    internal_record_id: str


class GetNumberOfVersionsRequestBody(G2PRequestBody):
    request_payload: GetNumberOfVersionsRequestPayload


class GetNumberOfVersionsRequest(G2PRequest):
    request_body: GetNumberOfVersionsRequestBody


class GetNumberOfPendingChangeRequestsRequestPayload(BaseModel):
    subject_register_id: str
    subject_record_id: str
    tab_id: str


class GetNumberOfPendingChangeRequestsRequestBody(G2PRequestBody):
    request_payload: GetNumberOfPendingChangeRequestsRequestPayload


class GetNumberOfPendingChangeRequestsRequest(G2PRequest):
    request_body: GetNumberOfPendingChangeRequestsRequestBody


class GetNumberOfCrossRegisterChangesRequestPayload(BaseModel):
    subject_register_id: str
    subject_record_id: str


class GetNumberOfCrossRegisterChangesRequestBody(G2PRequestBody):
    request_payload: GetNumberOfCrossRegisterChangesRequestPayload


class GetNumberOfCrossRegisterChangesRequest(G2PRequest):
    request_body: GetNumberOfCrossRegisterChangesRequestBody


class GetCrossRegisterChangesRequestPayload(BaseModel):
    subject_register_id: str
    subject_record_id: str


class GetCrossRegisterChangesRequestBody(G2PRequestBody):
    request_payload: GetCrossRegisterChangesRequestPayload


class GetCrossRegisterChangesRequest(G2PRequest):
    request_body: GetCrossRegisterChangesRequestBody


class GetChangeRequestsRequestPayload(BaseModel):
    subject_register_id: str
    subject_record_id: str
    tab_id: str


class GetChangeRequestsRequestBody(G2PRequestBody):
    request_payload: GetChangeRequestsRequestPayload


class GetChangeRequestsRequest(G2PRequest):
    request_body: GetChangeRequestsRequestBody


class GetChangeRequestRequestPayload(BaseModel):
    change_request_id: str


class GetChangeRequestRequestBody(G2PRequestBody):
    request_payload: GetChangeRequestRequestPayload


class GetChangeRequestRequest(G2PRequest):
    request_body: GetChangeRequestRequestBody


class GetSubjectRecordRequestPayload(BaseModel):
    subject_register_id: str
    subject_record_id: str


class GetSubjectRecordRequestBody(G2PRequestBody):
    request_payload: GetSubjectRecordRequestPayload


class GetSubjectRecordRequest(G2PRequest):
    request_body: GetSubjectRecordRequestBody


class GetVerificationsRequestPayload(BaseModel):
    change_request_id: str


class GetVerificationsRequestBody(G2PRequestBody):
    request_payload: GetVerificationsRequestPayload


class GetVerificationsRequest(G2PRequest):
    request_body: GetVerificationsRequestBody


class GetDeduplicationRegisterResultsRequestPayload(BaseModel):
    change_request_id: str


class GetDeduplicationRegisterResultsRequestBody(G2PRequestBody):
    request_payload: GetDeduplicationRegisterResultsRequestPayload


class GetDeduplicationRegisterResultsRequest(G2PRequest):
    request_body: GetDeduplicationRegisterResultsRequestBody


class GetDeduplicationChangerequestResultsRequestPayload(BaseModel):
    change_request_id: str


class GetDeduplicationChangerequestResultsRequestBody(G2PRequestBody):
    request_payload: GetDeduplicationChangerequestResultsRequestPayload


class GetDeduplicationChangerequestResultsRequest(G2PRequest):
    request_body: GetDeduplicationChangerequestResultsRequestBody


class AddVerificationRequestBody(G2PRequestBody):
    request_payload: AddVerificationPayload


class AddVerificationRequest(G2PRequest):
    request_body: AddVerificationRequestBody


class IngestDataRequest(Request):
    # Request struture is internal to partners
    pass


class GetRegisterSchemaRequestPayload(BaseModel):
    register_id: str


class GetRegisterSchemaRequestBody(G2PRequestBody):
    request_payload: GetRegisterSchemaRequestPayload


class GetRegisterSchemaRequest(G2PRequest):
    request_body: GetRegisterSchemaRequestBody


class GetRegisterSectionsRequestPayload(BaseModel):
    register_id: str


class GetRegisterSectionsRequestBody(G2PRequestBody):
    request_payload: GetRegisterSectionsRequestPayload


class GetRegisterSectionsRequest(G2PRequest):
    request_body: GetRegisterSectionsRequestBody


class GetRegisterTabSectionsRequestPayload(BaseModel):
    register_id: str
    tab_id: str


class GetRegisterTabSectionsRequestBody(G2PRequestBody):
    request_payload: GetRegisterTabSectionsRequestPayload


class GetRegisterTabSectionsRequest(G2PRequest):
    request_body: GetRegisterTabSectionsRequestBody


class GetRegisterTabsRequestPayload(BaseModel):
    register_id: str


class GetRegisterTabsRequestBody(G2PRequestBody):
    request_payload: GetRegisterTabsRequestPayload


class GetRegisterTabsRequest(G2PRequest):
    request_body: GetRegisterTabsRequestBody


class AddRegisterTabRequestPayload(BaseModel):
    register_id: str
    tab_label: str
    tab_order: int = 0


class AddRegisterTabRequestBody(G2PRequestBody):
    request_payload: AddRegisterTabRequestPayload


class AddRegisterTabRequest(G2PRequest):
    request_body: AddRegisterTabRequestBody


class DeleteRegisterTabRequestPayload(BaseModel):
    tab_id: str


class DeleteRegisterTabRequestBody(G2PRequestBody):
    request_payload: DeleteRegisterTabRequestPayload


class DeleteRegisterTabRequest(G2PRequest):
    request_body: DeleteRegisterTabRequestBody


class GetRegisterSectionRequestPayload(BaseModel):
    register_id: str
    section_id: str


class GetRegisterSectionRequestBody(G2PRequestBody):
    request_payload: GetRegisterSectionRequestPayload


class GetRegisterSectionRequest(G2PRequest):
    request_body: GetRegisterSectionRequestBody


class AddRegisterSectionRequestPayload(BaseModel):
    section_register_id: str
    register_id: str
    tab_id: str
    section_mnemonic: str
    section_description: Optional[str] = None
    documents_required: bool = False
    no_of_verifications_required: int = 0
    auto_approval: bool = False
    is_list: bool = False
    section_ui_schema: Optional[dict] = None


class AddRegisterSectionRequestBody(G2PRequestBody):
    request_payload: AddRegisterSectionRequestPayload


class AddRegisterSectionRequest(G2PRequest):
    request_body: AddRegisterSectionRequestBody


class DeleteRegisterSectionRequestPayload(BaseModel):
    register_id: str
    section_id: str


class DeleteRegisterSectionRequestBody(G2PRequestBody):
    request_payload: DeleteRegisterSectionRequestPayload


class DeleteRegisterSectionRequest(G2PRequest):
    request_body: DeleteRegisterSectionRequestBody


class UpdateRegisterSectionRequestPayload(BaseModel):
    register_id: str
    section_id: str
    tab_id: Optional[str] = None
    section_mnemonic: Optional[str] = None
    section_description: Optional[str] = None
    documents_required: Optional[bool] = None
    no_of_verifications_required: Optional[int] = None
    auto_approval: Optional[bool] = None
    is_list: Optional[bool] = None


class UpdateRegisterSectionRequestBody(G2PRequestBody):
    request_payload: UpdateRegisterSectionRequestPayload


class UpdateRegisterSectionRequest(G2PRequest):
    request_body: UpdateRegisterSectionRequestBody


class UpdateRegisterSectionUISchemaRequestPayload(BaseModel):
    register_id: str
    section_id: str
    section_ui_schema: Optional[dict] = None


class UpdateRegisterSectionUISchemaRequestBody(G2PRequestBody):
    request_payload: UpdateRegisterSectionUISchemaRequestPayload


class UpdateRegisterSectionUISchemaRequest(G2PRequest):
    request_body: UpdateRegisterSectionUISchemaRequestBody


class CreateRegisterRequestPayload(BaseModel):
    register_mnemonic: str
    register_description: Optional[str] = None
    master_register_id: Optional[str] = None
    dedup_is_enabled: bool = False
    dedup_threshold_score: Optional[float] = None


class CreateRegisterRequestBody(G2PRequestBody):
    request_payload: CreateRegisterRequestPayload


class CreateRegisterRequest(G2PRequest):
    request_body: CreateRegisterRequestBody


class UpdateRegisterSchemaRequestPayload(BaseModel):
    register_id: str
    deduplicate_schema: Optional[list[dict]] = None
    search_result_schema: Optional[list[dict]] = None
    filter_schema: Optional[list[dict]] = None


class UpdateRegisterSchemaRequestBody(G2PRequestBody):
    request_payload: UpdateRegisterSchemaRequestPayload


class UpdateRegisterSchemaRequest(G2PRequest):
    request_body: UpdateRegisterSchemaRequestBody


# Deduplication Configuration APIs - split from UpdateRegisterSchema
class UpdateDedupIsEnabledRequestPayload(BaseModel):
    register_id: str
    dedup_is_enabled: bool


class UpdateDedupIsEnabledRequestBody(G2PRequestBody):
    request_payload: UpdateDedupIsEnabledRequestPayload


class UpdateDedupIsEnabledRequest(G2PRequest):
    request_body: UpdateDedupIsEnabledRequestBody


class UpdateDedupThresholdScoreRequestPayload(BaseModel):
    register_id: str
    dedup_threshold_score: float


class UpdateDedupThresholdScoreRequestBody(G2PRequestBody):
    request_payload: UpdateDedupThresholdScoreRequestPayload


class UpdateDedupThresholdScoreRequest(G2PRequest):
    request_body: UpdateDedupThresholdScoreRequestBody


class UpdateDeduplicationSchemaRequestPayload(BaseModel):
    register_id: str
    deduplicate_schema: list[dict]


class UpdateDeduplicationSchemaRequestBody(G2PRequestBody):
    request_payload: UpdateDeduplicationSchemaRequestPayload


class UpdateDeduplicationSchemaRequest(G2PRequest):
    request_body: UpdateDeduplicationSchemaRequestBody


class UpdateSearchResultSchemaRequestPayload(BaseModel):
    register_id: str
    search_result_schema: list[dict]


class UpdateSearchResultSchemaRequestBody(G2PRequestBody):
    request_payload: UpdateSearchResultSchemaRequestPayload


class UpdateSearchResultSchemaRequest(G2PRequest):
    request_body: UpdateSearchResultSchemaRequestBody


class GetSectionRecordsRequestPayload(BaseModel):
    subject_register_id: str
    subject_record_id: str
    section_register_id: str


class GetSectionRecordsRequestBody(G2PRequestBody):
    request_payload: GetSectionRecordsRequestPayload


class GetSectionRecordsRequest(G2PRequest):
    request_body: GetSectionRecordsRequestBody


class GetRegisterTabRecordsRequestPayload(BaseModel):
    subject_register_id: str
    subject_record_id: str
    tab_id: str


class GetRegisterTabRecordsRequestBody(G2PRequestBody):
    request_payload: GetRegisterTabRecordsRequestPayload


class GetRegisterTabRecordsRequest(G2PRequest):
    request_body: GetRegisterTabRecordsRequestBody
