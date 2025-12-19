import enum
from operator import index
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


class G2PRegisterChangeLog(BaseORMModel):
    __tablename__ = "g2p_register_change_logs"

    change_log_id: Mapped[str] = mapped_column(String, primary_key=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    internal_record_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_partner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
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
    deduplication_changelog_status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=DeduplicationStatusEnum.PENDING.value,
        index=True
    )
    deduplication_changelog_failure_reason: Mapped[str] = mapped_column(String, nullable=True)


class G2PRegisterChangeLogPayload(BaseORMModel):
    __tablename__ = "g2p_register_change_log_payloads"

    change_log_id: Mapped[str] = mapped_column(String, ForeignKey("g2p_register_change_logs.change_log_id"), primary_key=True)
    change_payload: Mapped[JSON] = mapped_column(JSON, nullable=False)
    search_text: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index('ix_g2p_register_change_log_payloads_search_text_gin', 'search_text', postgresql_using='gin', postgresql_ops={'search_text': 'gin_trgm_ops'}),
    )

    @validates('change_payload')
    def update_search_text(self, key, value):
        """Automatically populate search_text from change_payload JSON"""
        if value:
            # Convert JSON to string representation for searching
            if isinstance(value, dict):
                self.search_text = json.dumps(value)
            else:
                self.search_text = str(value)
        return value


class G2PRegisterChangeLogDocuments(BaseORMModel):
    __tablename__ = "g2p_register_change_log_documents"

    document_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    change_log_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    document_store_id: Mapped[str] = mapped_column(String, nullable=False)

