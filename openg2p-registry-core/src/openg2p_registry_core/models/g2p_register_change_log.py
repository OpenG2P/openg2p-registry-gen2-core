import enum
from operator import index
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel

class ApprovalStatusEnum(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class G2PRegisterChangeLog(BaseORMModel):
    __tablename__ = "g2p_register_change_logs"

    change_log_id: Mapped[str] = mapped_column(String, primary_key=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    internal_record_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    operation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    change_payload: Mapped[JSON] = mapped_column(JSON, nullable=False)
    source_partner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    no_of_verifications_required: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    no_of_verifications_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approval_status: Mapped[str] = mapped_column(String, nullable=False, default=ApprovalStatusEnum.PENDING.value)
    approved_by: Mapped[str] = mapped_column(String, nullable=True)
    approved_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

class G2PRegisterChangeLogDocuments(BaseORMModel):
    __tablename__ = "g2p_register_change_log_documents"

    document_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    change_log_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    document_store_id: Mapped[str] = mapped_column(String, nullable=False)

