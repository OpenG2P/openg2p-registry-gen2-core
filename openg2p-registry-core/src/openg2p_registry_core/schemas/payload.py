from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from ..models import ApprovalStatusEnum


class RegisterPayload(BaseModel):
    pass


class RegisterSummaryData(BaseModel):
    register_id: str
    register_mnemonic: str
    register_subject: Optional[str] = None
    total_record_count: int


class RegisterData(BaseModel):
    register_id: str
    register_mnemonic: str
    register_subject: Optional[str] = None
    register_description: Optional[str] = None
    master_register_id: Optional[str] = None


class ChildRegisterData(BaseModel):
    register_id: str
    register_mnemonic: str
    register_subject: Optional[str] = None
    register_description: Optional[str] = None


class SearchResultData(BaseModel):
    internal_record_id: str
    functional_record_id: str
    link_record_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    last_approved_at: Optional[str] = None
    last_approved_by: Optional[str] = None
    additional_fields: Optional[dict] = None

    class Config:
        from_attributes: bool = True


class RecordData(BaseModel):
    internal_record_id: str
    functional_record_id: str
    link_record_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    last_approved_at: Optional[str] = None
    last_approved_by: Optional[str] = None
    additional_fields: Optional[dict] = None

    class Config:
        from_attributes: bool = True


class ChangeLogSearchResultData(BaseModel):
    change_log_id: str
    register_id: str
    internal_record_id: str
    operation_id: str
    source_partner_id: str
    created_by: str
    created_at: Optional[str] = None
    no_of_verifications_required: Optional[int] = None
    no_of_verifications_done: Optional[int] = None
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    change_payload: Optional[dict] = None

    class Config:
        from_attributes: bool = True


class ChangeLogPayload(RegisterPayload):
    register_id: Optional[str] = None
    register_mnemonic: Optional[str] = None
    operation_id: Optional[str] = None
    change_payload: Optional[dict] = None

    # Not sent from Partners
    no_of_verifications_required: Optional[int] = 0
    no_of_verifications_done: Optional[int] = 0
    approval_status: ApprovalStatusEnum = ApprovalStatusEnum.PENDING
    change_log_id: Optional[str] = None
    internal_record_id: Optional[str] = None

    created_by: Optional[str] = None
    created_at: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


class NumberOfVersionsData(BaseModel):
    register_id: str
    internal_record_id: str
    number_of_versions: int


class NumberOfPendingChangeLogsData(BaseModel):
    register_id: str
    internal_record_id: str
    number_of_pending_change_logs: int


class ChangeLogData(BaseModel):
    change_log_id: str
    register_id: str
    internal_record_id: str
    operation_id: str
    source_partner_id: str
    created_by: str
    created_at: Optional[str] = None
    no_of_verifications_required: Optional[int] = None
    no_of_verifications_done: Optional[int] = None
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    change_payload: Optional[dict] = None

    class Config:
        from_attributes: bool = True


class ChangeLogsData(BaseModel):
    change_logs: List[ChangeLogData]

    class Config:
        from_attributes: bool = True


class VerificationData(BaseModel):
    verification_id: str
    register_id: str
    internal_record_id: str
    operation_id: str
    change_log_id: str
    verified_by: str
    verified_at: Optional[str] = None
    verification_observations: Optional[str] = None
    is_approved: bool

    class Config:
        from_attributes: bool = True


class VerificationsData(BaseModel):
    verifications: List[VerificationData]

    class Config:
        from_attributes: bool = True


class AddVerificationPayload(BaseModel):
    change_log_id: str
    verification_observations: Optional[str] = None
    is_approved: bool


class IngestDataPayload(BaseModel):
    ingest_id: str