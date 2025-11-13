from enum import unique
from operator import index
from site import venv
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegisterDefinition(BaseORMModel):
    __tablename__ = "g2p_register_definitions"

    register_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    register_mnemonic: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    register_description: Mapped[Text] = mapped_column(Text, nullable=True)
    master_register_id: Mapped[str] = mapped_column(String, nullable=True, index=True)


class G2PRegisterOperation(BaseORMModel):
    __tablename__ = "g2p_register_operations"

    operation_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    operation_mnemonic: Mapped[str] = mapped_column(String, nullable=False, index=True)
    operation_description: Mapped[Text] = mapped_column(Text, nullable=True)
    json_form_schema: Mapped[JSON] = mapped_column(JSON, nullable=False)
    documents_required: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=False)
    no_of_verifications_required: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_approval: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=False)
    is_new_operation: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=True)