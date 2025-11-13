from enum import unique
from operator import index
from site import venv
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegisterVerification(BaseORMModel):
    __tablename__ = "g2p_register_verifications"

    verification_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    internal_record_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    operation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    change_log_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    verified_by: Mapped[str] = mapped_column(String, nullable=False)
    verified_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    verification_observations: Mapped[Text] = mapped_column(Text, nullable=True)