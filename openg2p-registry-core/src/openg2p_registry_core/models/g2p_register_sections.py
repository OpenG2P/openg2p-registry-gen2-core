import uuid
from sqlalchemy import String, ForeignKey, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegisterSection(BaseORMModel):
    """
    Stores section UI schema configurations for each register.
    Composite primary key: register_id + section_id
    """
    __tablename__ = "g2p_register_sections"

    register_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("g2p_register_definitions.register_id"),
        primary_key=True,
        index=True
    )
    section_id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    section_mnemonic: Mapped[str] = mapped_column(String, nullable=False, index=True)
    section_description: Mapped[Text] = mapped_column(Text, nullable=True)
    json_form_schema: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
    documents_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    no_of_verifications_required: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_new_section: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Section UI schema configuration (JSONB for PostgreSQL)
    # JSON structure to define UI rendering for this section
    section_ui_schema: Mapped[dict] = mapped_column(JSONB, nullable=True)
