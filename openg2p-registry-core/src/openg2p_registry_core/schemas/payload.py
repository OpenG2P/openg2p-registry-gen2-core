from typing import Optional, List
from pydantic import BaseModel

from ..models import ApprovalStatusEnum


class RegisterPayload(BaseModel):
    pass


class RegisterSummaryData(BaseModel):
    register_id: str
    register_mnemonic: str
    register_subject: Optional[str] = None
    total_record_count: int


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
