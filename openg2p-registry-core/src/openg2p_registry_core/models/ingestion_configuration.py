from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class IncomingPartners(BaseORMModel):
   
    __tablename__ = "incoming_partners"

    partner_id: Mapped[str] = mapped_column(String, primary_key=True)
    partner_mnemonic: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    keymanager_reference_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)

class IncomingModelSignaturePattern(BaseORMModel):
    
    __tablename__ = "incoming_model_signature_patterns"
    signature_pattern_id: Mapped[str] = mapped_column(String, primary_key=True)
    partner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pattern_for_sender: Mapped[str] = mapped_column(String, nullable=False)
    pattern_for_signature: Mapped[str] = mapped_column(String, nullable=False)
    pattern_for_data_model: Mapped[str] = mapped_column(String, nullable=False)

class IncomingModelSemanticPattern(BaseORMModel):
    
    __tablename__ = "incoming_model_semantic_patterns"

    semantic_pattern_id: Mapped[str] = mapped_column(String, primary_key=True)
    data_model_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pattern : Mapped[str] = mapped_column(String, nullable=False)
    inbound_register_id: Mapped[str] = mapped_column(String, nullable=False)
    inbound_operation_id: Mapped[str] = mapped_column(String, nullable=False)

class IncomingTemplate(BaseORMModel):
    
    __tablename__ = "incoming_templates"

    template_id: Mapped[str] = mapped_column(String, primary_key=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    operation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    data_model_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    template_file: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('register_id', 'operation_id', 'data_model_id', name='uix_register_operation_data_model'),
    )


class IncomingFactoryClass(BaseORMModel):

    __tablename__ = "incoming_factory_classes"

    incoming_factory_id: Mapped[str] = mapped_column(String, primary_key=True)
    partner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    operation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    business_processing_class: Mapped[str] = mapped_column(String, nullable=False)
    