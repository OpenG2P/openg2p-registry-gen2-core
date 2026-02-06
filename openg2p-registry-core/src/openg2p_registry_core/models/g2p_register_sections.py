import uuid
from sqlalchemy import String, ForeignKey, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegisterSection(BaseORMModel):
    """
    Stores section UI schema configurations for each register.
    Primary key: section_id
    """
    __tablename__ = "g2p_register_sections"

    register_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )
    tab_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )
    section_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    section_register_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )
    is_primary_section: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    section_mnemonic: Mapped[str] = mapped_column(String, nullable=False, index=True)
    section_description: Mapped[Text] = mapped_column(Text, nullable=True)
    documents_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    no_of_verifications_required: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_list: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Section UI schema configuration (JSONB for PostgreSQL)
    # JSON structure to define UI rendering for this section
    section_ui_schema: Mapped[dict] = mapped_column(JSONB, nullable=True)

    
class G2PRegisterSectionDocument(BaseORMModel):
    __tablename__ = "g2p_register_section_documents"

    document_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    internal_record_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )
    register_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )
    section_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )
    document_label: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )
    document_store_id: Mapped[str] = mapped_column(String, nullable=False)
