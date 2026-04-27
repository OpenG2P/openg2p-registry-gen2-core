import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegisterScore(BaseORMModel):
    """
    Latest computed score per record per score_type.
    Upsert key: (internal_record_id, score_type)
    """

    __tablename__ = "g2p_register_scores"

    score_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    internal_record_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    score_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    score_definition_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Change Request that last triggered this computation
    triggered_by_cr_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    computed_score: Mapped[float] = mapped_column(Float, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        # Used by the upsert logic in the compute worker.
        Index(
            "ix_g2p_register_scores_internal_record_score_type_unique",
            "internal_record_id",
            "score_type",
            unique=True,
        ),
    )

