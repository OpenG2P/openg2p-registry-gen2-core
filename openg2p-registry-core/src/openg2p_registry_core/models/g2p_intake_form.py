import uuid

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy.dialects.postgresql import UUID

from .enum import ApprovalStatusEnum, ChangeRequestSourceEnum, IntakeFormStatusEnum, ProcessStatusEnum


class G2PIntakeForm(BaseORMModel):
    __abstract__ = True

    submission_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))


# Backward-compatible alias for the previous typo.
G2PIntakeFrom = G2PIntakeForm


class G2PIntakeFormSubmission(BaseORMModel):
    __tablename__ = "g2p_intake_form_submissions"

    submission_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    draft_status: Mapped[IntakeFormStatusEnum] = mapped_column(
        String,
        nullable=False,
        default=IntakeFormStatusEnum.DRAFT.value,
    )
    approval_status: Mapped[ApprovalStatusEnum] = mapped_column(
        String,
        nullable=False,
        default=ApprovalStatusEnum.PENDING.value,
    )
    approved_by: Mapped[str] = mapped_column(String, nullable=True)
    approved_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    remarks: Mapped[str] = mapped_column(Text, nullable=True)
    finalized_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    first_created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    last_updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    created_by: Mapped[str] = mapped_column(String, nullable=False)
    submission_source: Mapped[ChangeRequestSourceEnum] = mapped_column(String, nullable=False)
    partner_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    register_ingest_process_status: Mapped[ProcessStatusEnum] = mapped_column(
        String,
        nullable=False,
        default=ProcessStatusEnum.NOT_APPLICABLE.value,
    )
    register_ingest_processed_timestamp: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    register_ingest_process_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    register_ingest_process_last_error_code: Mapped[str] = mapped_column(Text, nullable=True)
    number_of_verifications_required: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    number_of_verifications_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


G2PIntakeFormSubmissions = G2PIntakeFormSubmission


class G2PIntakeFormSubmissionPayload(BaseORMModel):
    __tablename__ = "g2p_intake_form_submission_payloads"

    submission_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    search_text: Mapped[str] = mapped_column(Text, nullable=True)


class G2PIntakeFormSubmissionDocument(BaseORMModel):
    __tablename__ = "g2p_intake_form_submission_documents"

    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    document_label: Mapped[str] = mapped_column(String, nullable=False)
    document_store_id: Mapped[str] = mapped_column(String, nullable=False)


G2PIntakeFormSectionPayload = G2PIntakeFormSubmissionPayload
G2PIntakeFormSectionDocuments = G2PIntakeFormSubmissionDocument
