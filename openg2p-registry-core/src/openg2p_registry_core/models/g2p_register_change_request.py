import enum
import uuid
import json

from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, validates
from openg2p_fastapi_common.models import BaseORMModel

class ApprovalStatusEnum(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DeduplicationStatusEnum(enum.Enum):
    PENDING = "PENDING"
    INPROGRESS = "INPROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ChangeRequestSourceEnum(enum.Enum):
    INTAKE_FORM = "INTAKE_FORM"
    DIRECT = "DIRECT"

class G2PRegisterChangeRequest(BaseORMModel):
    __tablename__ = "g2p_register_change_requests"

    change_request_id: Mapped[str] = mapped_column(String, primary_key=True)
    record_name: Mapped[str] = mapped_column(String, nullable=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    tab_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    is_primary_section: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    section_register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    internal_record_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_partner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    
    change_request_source: Mapped[ChangeRequestSourceEnum] = mapped_column(String, nullable=False)
    submission_id: Mapped[str] = mapped_column(String, nullable=True, index=True)

    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    
    no_of_verifications_required: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    no_of_verifications_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    approval_status: Mapped[str] = mapped_column(String, nullable=False, default=ApprovalStatusEnum.PENDING.value)
    approved_by: Mapped[str] = mapped_column(String, nullable=True)
    approved_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    # Deduplication status fields
    deduplication_register_status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=DeduplicationStatusEnum.PENDING.value,
        index=True
    )
    deduplication_register_failure_reason: Mapped[str] = mapped_column(String, nullable=True)
    deduplication_change_request_status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=DeduplicationStatusEnum.PENDING.value,
        index=True
    )
    deduplication_change_request_failure_reason: Mapped[str] = mapped_column(String, nullable=True)


class G2PRegisterChangeRequestPayload(BaseORMModel):
    __tablename__ = "g2p_register_change_request_payloads"

    change_request_id: Mapped[str] = mapped_column(String, primary_key=True)
    record_name: Mapped[str] = mapped_column(String, nullable=True)
    change_payload: Mapped[JSON] = mapped_column(JSON, nullable=False)
    search_text: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index('ix_g2p_register_change_request_payloads_search_text_gin', 'search_text', postgresql_using='gin', postgresql_ops={'search_text': 'gin_trgm_ops'}),
    )

    @validates('change_payload')
    def update_search_text(self, key, value):
        """Automatically populate search_text from change_payload JSON (array of payloads)"""
        if value:
            # Convert JSON to string representation for searching
            if isinstance(value, (dict, list)):
                self.search_text = json.dumps(value)
            else:
                self.search_text = str(value)
        return value


class G2PRegisterChangeRequestDocument(BaseORMModel):
    __tablename__ = "g2p_register_change_request_documents"

    document_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    change_request_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    document_label: Mapped[str] = mapped_column(String, nullable=False, index=True)
    document_store_id: Mapped[str] = mapped_column(String, nullable=False)
