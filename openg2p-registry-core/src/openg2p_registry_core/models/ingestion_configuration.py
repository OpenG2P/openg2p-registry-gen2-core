from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class IncomingPartner(BaseORMModel):
   
    __tablename__ = "incoming_partners"

    partner_id: Mapped[str] = mapped_column(String, primary_key=True)
    partner_mnemonic: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    keymanager_reference_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class IncomingModelSignaturePattern(BaseORMModel):
    
    __tablename__ = "incoming_model_signature_patterns"
    signature_pattern_id: Mapped[str] = mapped_column(String, primary_key=True)
    data_model_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    key_path_for_sender: Mapped[str] = mapped_column(String, nullable=False)
    key_path_for_signature: Mapped[str] = mapped_column(String, nullable=False)

class IncomingModelSemanticPattern(BaseORMModel):
    
    __tablename__ = "incoming_model_semantic_patterns"

    semantic_pattern_id: Mapped[str] = mapped_column(String, primary_key=True)
    data_model_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False)
    operation_id: Mapped[str] = mapped_column(String, nullable=False)
    pattern_for_register: Mapped[str] = mapped_column(String, nullable=False)
    pattern_for_operation: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('data_model_id', 'register_id', 'operation_id', name='uix_dro_1'),
    )

class IncomingTemplate(BaseORMModel):
    
    __tablename__ = "incoming_templates"

    template_id: Mapped[str] = mapped_column(String, primary_key=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    operation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    data_model_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    template_file_id: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('data_model_id', 'register_id', 'operation_id', name='uix_dro_2'),
    )

class IncomingPayloadEnricher(BaseORMModel):

    __tablename__ = "incoming_payload_enrichers"

    incoming_factory_id: Mapped[str] = mapped_column(String, primary_key=True)
    data_model_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    operation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    raw_payload_enricher_class: Mapped[str] = mapped_column(String, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('data_model_id', 'register_id', 'operation_id', name='uix_dro_3'),
    )
