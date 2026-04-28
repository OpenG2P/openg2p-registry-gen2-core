
from typing import Any, List, Optional

from openg2p_fastapi_common.schemas import G2PRequest, G2PRequestBody, G2PResponse, G2PResponseBody
from pydantic import BaseModel, ConfigDict


class G2PIntakeFormSchemaBase:
    submission_id: Optional[str] = None


class IntakeFormDocumentPayload(BaseModel):
    document_label: str
    document_store_id: str


class IntakeFormData(BaseModel):
    submission_id: Optional[str] = None
    form_id: Optional[str] = None
    register_id: Optional[str] = None
    draft_status: Optional[str] = None
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    finalized_at: Optional[str] = None
    first_created_at: Optional[str] = None
    submission_source: Optional[str] = None
    partner_id: Optional[str] = None
    register_ingest_process_status: Optional[str] = None
    register_ingest_processed_timestamp: Optional[str] = None
    register_ingest_process_attempts: Optional[int] = None
    register_ingest_process_last_error_code: Optional[str] = None
    number_of_verifications_required: Optional[int] = None
    number_of_verifications_done: Optional[int] = None
    created_by: Optional[str] = None
    last_updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SectionPayloadResponseItem(BaseModel):
    section_id: str
    section_register_id: str
    is_list: bool
    records: List[dict]
    documents: Optional[List[IntakeFormDocumentPayload]] = None


class SubmissionResponsePayload(IntakeFormData):
    record_name: Optional[str] = None
    section_payloads: Optional[List[SectionPayloadResponseItem]] = None


class SectionPayloadInput(BaseModel):
    section_id: str
    intake_form_section_payload: List[dict]
    documents: Optional[List[IntakeFormDocumentPayload]] = None


class SaveIntakeFormSubmissionRequestPayload(BaseModel):
    submission_id: Optional[str] = None
    section_id: str
    section_payload: List[dict]
    section_register_id: str
    form_id: str
    register_id: str
    created_by: Optional[str] = None


class SaveIntakeFormSubmissionRequestBody(G2PRequestBody):
    request_payload: SaveIntakeFormSubmissionRequestPayload


class SaveIntakeFormSubmissionRequest(G2PRequest):
    request_body: SaveIntakeFormSubmissionRequestBody


class SaveSubmissionDraftRequestPayload(BaseModel):
    submission_id: Optional[str] = None
    form_id: str
    register_id: str
    submission_source: Optional[str] = None
    partner_id: Optional[str] = None
    section_payloads: Optional[List[SectionPayloadInput]] = None
    created_by: Optional[str] = None


class DeleteIntakeFormSubmissionRequestPayload(BaseModel):
    submission_id: str


class FinalizeSubmissionRequestPayload(BaseModel):
    submission_id: str


class ApproveRejectSubmissionRequestPayload(BaseModel):
    submission_id: str
    approved_by: Optional[str] = None


class GetSubmissionRequestPayload(BaseModel):
    submission_id: str
    section_register_id: str
    register_id: str
    section_id: str


class SearchInSubmissionRequestPayload(BaseModel):
    register_id: str
    search_text: Optional[str] = None
    current_page: int = 1
    page_size: int = 10
    sort_by: Optional[str] = None
    filter_by: Optional[dict[str, Any]] = None


class SaveSubmissionDraftRequestBody(G2PRequestBody):
    request_payload: SaveSubmissionDraftRequestPayload


class SaveSubmissionDraftRequest(G2PRequest):
    request_body: SaveSubmissionDraftRequestBody


class DeleteIntakeFormSubmissionRequestBody(G2PRequestBody):
    request_payload: DeleteIntakeFormSubmissionRequestPayload


class DeleteIntakeFormSubmissionRequest(G2PRequest):
    request_body: DeleteIntakeFormSubmissionRequestBody


class FinalizeSubmissionRequestBody(G2PRequestBody):
    request_payload: FinalizeSubmissionRequestPayload


class FinalizeSubmissionRequest(G2PRequest):
    request_body: FinalizeSubmissionRequestBody


class ApproveRejectSubmissionRequestBody(G2PRequestBody):
    request_payload: ApproveRejectSubmissionRequestPayload


class ApproveRejectSubmissionRequest(G2PRequest):
    request_body: ApproveRejectSubmissionRequestBody


class GetSubmissionRequestBody(G2PRequestBody):
    request_payload: GetSubmissionRequestPayload


class GetSubmissionRequest(G2PRequest):
    request_body: GetSubmissionRequestBody


class SearchInSubmissionRequestBody(G2PRequestBody):
    request_payload: SearchInSubmissionRequestPayload


class SearchInSubmissionRequest(G2PRequest):
    request_body: SearchInSubmissionRequestBody


class SubmissionResponseBody(G2PResponseBody):
    response_payload: Optional[SubmissionResponsePayload] = None


class SubmissionResponse(G2PResponse):
    response_body: Optional[SubmissionResponseBody] = None


class SubmissionSearchResultsResponseBody(G2PResponseBody):
    response_payload: Optional[List[SubmissionResponsePayload]] = None


class SubmissionSearchResultsResponse(G2PResponse):
    response_body: Optional[SubmissionSearchResultsResponseBody] = None
