import uuid
from datetime import datetime

from sqlalchemy import String, Float, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class DeduplicationRegisterResult(BaseORMModel):
    """
    Stores deduplication results when comparing a change log against existing register records.
    """
    __tablename__ = "deduplication_register_results"

    dedup_result_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    change_log_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    internal_record_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    field_matches: Mapped[JSON] = mapped_column(JSON, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_dedup_register_change_log_id', 'change_log_id'),
        Index('idx_dedup_register_internal_record_id', 'internal_record_id'),
    )


class DeduplicationChangelogResult(BaseORMModel):
    """
    Stores deduplication results when comparing a change log against other pending change logs.
    """
    __tablename__ = "deduplication_changelog_results"

    dedup_result_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    change_log_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    candidate_change_log_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    field_matches: Mapped[JSON] = mapped_column(JSON, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_dedup_changelog_change_log_id', 'change_log_id'),
        Index('idx_dedup_changelog_candidate_change_log_id', 'candidate_change_log_id'),
    )

