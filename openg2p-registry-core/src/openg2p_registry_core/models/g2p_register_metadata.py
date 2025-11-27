from enum import unique
from operator import index
from site import venv
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, validates
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegisterDefinition(BaseORMModel):
    __tablename__ = "g2p_register_definitions"

    register_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    register_mnemonic: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    register_subject: Mapped[str] = mapped_column(String, nullable=True)
    register_description: Mapped[Text] = mapped_column(Text, nullable=True)
    master_register_id: Mapped[str] = mapped_column(String, nullable=True, index=True)

    # Deduplication configuration
    dedup_is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dedup_threshold_score: Mapped[float] = mapped_column(Float, nullable=True)
    dedup_fields_json: Mapped[JSON] = mapped_column(JSON, nullable=True)

    @validates('register_mnemonic')
    def set_register_subject(self, _key: str, register_mnemonic_value: str) -> str:
        """
        Automatically set register_subject to the plural form of register_mnemonic
        with the first letter capitalized.
        Example: 'farmer' -> 'Farmers'
        """
        if register_mnemonic_value:
            plural_form: str = register_mnemonic_value + 's'
            capitalized_plural: str = plural_form[0].upper() + plural_form[1:]
            self.register_subject = capitalized_plural
        return register_mnemonic_value


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