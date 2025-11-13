from typing import Optional
from pydantic import BaseModel

from ..models import ApprovalStatusEnum


class RegisterPayload(BaseModel):
    pass


class ChangeLogPayload(RegisterPayload):
    register_id: str
    register_mnemonic: str
    operation_id: str
    change_payload: dict

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
