from enum import unique, Enum
import json
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Index
from sqlalchemy.orm import validates
from sqlalchemy.orm import Mapped, mapped_column, synonym
from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy.dialects.postgresql import JSONB

from .g2p_register_change_request import ApprovalStatusEnum


class ChangeRequestStatusEnum(Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
   
class IntakeFormStatusEnum(Enum):
    DRAFT = "DRAFT"
    FINAL = "FINAL"


class G2PIntakeForm(BaseORMModel):
    __tablename__ = "g2p_intake_forms"

    intake_form_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    tab_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    foundational_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    link_foundational_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    intake_form_status: Mapped[IntakeFormStatusEnum] = mapped_column(String, nullable=False, default=IntakeFormStatusEnum.DRAFT.value)
    change_request_submission_status: Mapped[ChangeRequestStatusEnum] = mapped_column(String, nullable=False, default=ChangeRequestStatusEnum.NOT_APPLICABLE.value)
    change_request_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    submission_no_of_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    submission_latest_datetime: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    submission_latest_error_code: Mapped[str] = mapped_column(Text, nullable=True)

    no_of_verifications_required: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    no_of_verifications_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    approval_status: Mapped[str] = mapped_column(String, nullable=False, default=ApprovalStatusEnum.PENDING.value)
    approved_by: Mapped[str] = mapped_column(String, nullable=True)
    approved_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    last_updated_by: Mapped[str] = mapped_column(String, nullable=False)
    last_updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

class G2PIntakeFormSectionPayload(BaseORMModel):
    __tablename__ = "g2p_intake_form_section_payloads"
    intake_form_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    section_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    intake_form_payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    intake_form_json_text: Mapped[str] = mapped_column(Text, nullable=False)

    @validates('intake_form_payload_json')
    def update_intake_form_json_text(self, key, value):
        """Automatically populate intake_form_json_text from intake_form_payload_json JSON."""
        if value:
            # Convert JSON to string representation for searching
            if isinstance(value, dict):
                self.intake_form_json_text = json.dumps(value)
            else:
                self.intake_form_json_text = str(value)
        return value

    __table_args__ = (
        Index(
            'ix_g2p_intake_form_section_payloads_intake_form_json_text_gin',
            'intake_form_json_text',
            postgresql_using='gin',
            postgresql_ops={'intake_form_json_text': 'gin_trgm_ops'}
        ),
    )
