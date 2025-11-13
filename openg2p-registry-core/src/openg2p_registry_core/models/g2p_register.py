from enum import unique
from operator import index
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegister(BaseORMModel):
    __abstract__ = True
    __register_mnemonic__ = "g2p"

    internal_record_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    functional_record_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    link_record_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    last_updated_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    last_approved_by: Mapped[str] = mapped_column(String, nullable=True)