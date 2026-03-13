from enum import Enum
import re
import uuid
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, Index, BigInteger, event
from sqlalchemy.orm import Mapped, mapped_column, validates
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
    __tablename__ = "g2p_intake_form_submissions"

    submission_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_reference: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    record_name: Mapped[str] = mapped_column(String, nullable=True)
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
    submission_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    section_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    intake_form_section_payload: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    intake_form_section_text: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index(
            'ix_g2p_intake_form_section_payloads_search_text_gin',
            'intake_form_section_text',
            postgresql_using='gin',
            postgresql_ops={'intake_form_section_text': 'gin_trgm_ops'}
        ),
    )


class G2PIntakeFormSectionDocuments(BaseORMModel):
    __tablename__ = "g2p_intake_form_section_documents"
    
    document_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    submission_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    section_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    document_label: Mapped[str] = mapped_column(String, nullable=False)
    document_store_id: Mapped[str] = mapped_column(String, nullable=False)
