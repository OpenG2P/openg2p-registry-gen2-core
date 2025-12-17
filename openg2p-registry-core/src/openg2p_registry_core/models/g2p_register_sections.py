from sqlalchemy import String, ForeignKey
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
        primary_key=True
    )

    section_id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    # Section UI schema configuration (JSONB for PostgreSQL)
    # JSON structure to define UI rendering for this section
    section_ui_schema: Mapped[dict] = mapped_column(JSONB, nullable=True)

