from pydantic import BaseModel
from fastapi import Request
from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody
)
from .payload import ChangeLogPayload, AddVerificationPayload

class ChangeLogRequestBody(G2PRequestBody):
    request_payload: ChangeLogPayload

class ChangeLogRequest(G2PRequest):
    request_body: ChangeLogRequestBody


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


class GetChangeLogSummaryDataRequestBody(G2PRequestBody):
    request_payload: EmptyRequestPayload

class GetChangeLogSummaryDataRequest(G2PRequest):
    request_body: GetChangeLogSummaryDataRequestBody


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


class SearchChangeLogRequestPayload(BaseModel):
    pass


class SearchChangeLogRequestBody(G2PRequestBody):
    request_payload: SearchChangeLogRequestPayload


class SearchChangeLogRequest(G2PRequest):
    request_body: SearchChangeLogRequestBody


class GetChildRegistersRequestPayload(BaseModel):
    register_id: str


class GetChildRegistersRequestBody(G2PRequestBody):
    request_payload: GetChildRegistersRequestPayload


class GetChildRegistersRequest(G2PRequest):
    request_body: GetChildRegistersRequestBody


class GetNumberOfVersionsRequestPayload(BaseModel):
    register_id: str
    internal_record_id: str


class GetNumberOfVersionsRequestBody(G2PRequestBody):
    request_payload: GetNumberOfVersionsRequestPayload


class GetNumberOfVersionsRequest(G2PRequest):
    request_body: GetNumberOfVersionsRequestBody


class GetNumberOfPendingChangeLogsRequestPayload(BaseModel):
    register_id: str
    internal_record_id: str


class GetNumberOfPendingChangeLogsRequestBody(G2PRequestBody):
    request_payload: GetNumberOfPendingChangeLogsRequestPayload


class GetNumberOfPendingChangeLogsRequest(G2PRequest):
    request_body: GetNumberOfPendingChangeLogsRequestBody


class GetChangeLogsRequestPayload(BaseModel):
    register_id: str
    internal_record_id: str


class GetChangeLogsRequestBody(G2PRequestBody):
    request_payload: GetChangeLogsRequestPayload


class GetChangeLogsRequest(G2PRequest):
    request_body: GetChangeLogsRequestBody


class GetChangeLogRequestPayload(BaseModel):
    change_log_id: str


class GetChangeLogRequestBody(G2PRequestBody):
    request_payload: GetChangeLogRequestPayload


class GetChangeLogRequest(G2PRequest):
    request_body: GetChangeLogRequestBody


class GetRecordRequestPayload(BaseModel):
    register_id: str
    internal_record_id: str


class GetRecordRequestBody(G2PRequestBody):
    request_payload: GetRecordRequestPayload


class GetRecordRequest(G2PRequest):
    request_body: GetRecordRequestBody


class GetVerificationsRequestPayload(BaseModel):
    change_log_id: str


class GetVerificationsRequestBody(G2PRequestBody):
    request_payload: GetVerificationsRequestPayload


class GetVerificationsRequest(G2PRequest):
    request_body: GetVerificationsRequestBody


class GetDeduplicationRegisterResultsRequestPayload(BaseModel):
    change_log_id: str


class GetDeduplicationRegisterResultsRequestBody(G2PRequestBody):
    request_payload: GetDeduplicationRegisterResultsRequestPayload


class GetDeduplicationRegisterResultsRequest(G2PRequest):
    request_body: GetDeduplicationRegisterResultsRequestBody


class GetDeduplicationChangelogResultsRequestPayload(BaseModel):
    change_log_id: str


class GetDeduplicationChangelogResultsRequestBody(G2PRequestBody):
    request_payload: GetDeduplicationChangelogResultsRequestPayload


class GetDeduplicationChangelogResultsRequest(G2PRequest):
    request_body: GetDeduplicationChangelogResultsRequestBody


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
