import enum
import uuid

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class ChangeRequestSourceEnum(enum.Enum):
    APPLICATION = "APPLICATION"
    DIRECT = "DIRECT"

class G2PRegisterHistory(BaseORMModel):
    __abstract__ = True

    history_record_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    internal_record_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    functional_record_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    linked_internal_record_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    linked_internal_register_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    foundational_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    link_foundational_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    linked_foundational_register_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    record_name: Mapped[str] = mapped_column(String, nullable=True)
    record_image_storage_id: Mapped[str] = mapped_column(Text, nullable=True)
    administrative_area_large_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    administrative_area_small_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    change_request_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    tab_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    
    is_primary_section: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    application_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    change_request_source: Mapped[ChangeRequestSourceEnum] = mapped_column(String, nullable=False)

    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    approved_by: Mapped[str] = mapped_column(String, nullable=False)
    approved_at: Mapped[str] = mapped_column(DateTime, nullable=False)

class G2PRegisterDocumentHistory(BaseORMModel):
    __tablename__ = "g2p_register_document_history"

    document_history_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    internal_record_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    change_request_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    document_label_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    document_store_id: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    approved_by: Mapped[str] = mapped_column(String, nullable=False)
    approved_at: Mapped[str] = mapped_column(DateTime, nullable=False)