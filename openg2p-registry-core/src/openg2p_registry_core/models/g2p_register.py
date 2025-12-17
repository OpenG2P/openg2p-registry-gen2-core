from enum import unique
from operator import index
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegister(BaseORMModel):
    __abstract__ = True
    __register_mnemonic__ = "g2p"

    internal_record_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    functional_record_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    link_record_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    record_name: Mapped[str] = mapped_column(String, nullable=True)
    image: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    last_approved_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    last_approved_by: Mapped[str] = mapped_column(String, nullable=False)
    search_text: Mapped[str] = mapped_column(Text, nullable=True)

    @classmethod
    def __declare_last__(cls):
        """Create table-specific index after table is declared"""
        if not cls.__abstract__:
            # Create a unique index name based on the table name
            index_name = f"idx_{cls.__tablename__}_search_text_trigram"
            Index(index_name, cls.search_text, postgresql_using='gin', postgresql_ops={'search_text': 'gin_trgm_ops'}, table=cls.__table__)