from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class IncomingPartnerPayload(BaseModel):
    partner_id: Optional[str] = None
    partner_mnemonic: str
    keymanager_reference_id: str
    is_active: bool = True

    class Config:
        from_attributes: bool = True


class IncomingPartnerUpdatePayload(BaseModel):
    """Update payload for IncomingPartner - only allows updating specific fields"""
    partner_mnemonic: Optional[str] = None
    keymanager_reference_id: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes: bool = True


class IncomingPartnerData(BaseModel):
    partner_id: str
    partner_mnemonic: str
    keymanager_reference_id: str
    is_active: bool

    class Config:
        from_attributes: bool = True


class IncomingModelSignaturePatternPayload(BaseModel):
    signature_pattern_id: Optional[str] = None
    data_model_id: str
    key_path_for_sender: str
    key_path_for_signature: str
    key_path_for_signature_payload: str

    class Config:
        from_attributes: bool = True


class IncomingModelSignaturePatternUpdatePayload(BaseModel):
    """Update payload for IncomingModelSignaturePattern - only allows updating specific fields"""
    key_path_for_sender: Optional[str] = None
    key_path_for_signature: Optional[str] = None
    key_path_for_signature_payload: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingModelSignaturePatternData(BaseModel):
    signature_pattern_id: str
    data_model_id: str
    key_path_for_sender: str
    key_path_for_signature: str
    key_path_for_signature_payload: str

    class Config:
        from_attributes: bool = True


# IncomingModelSemanticPattern Schemas
class IncomingModelSemanticPatternPayload(BaseModel):
    semantic_pattern_id: Optional[str] = None
    data_model_id: str
    register_id: str
    operation_id: str
    pattern_for_register: str
    pattern_for_operation: str

    class Config:
        from_attributes: bool = True


class IncomingModelSemanticPatternUpdatePayload(BaseModel):
    """Update payload for IncomingModelSemanticPattern - only allows updating specific fields"""
    pattern_for_register: Optional[str] = None
    pattern_for_operation: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingModelSemanticPatternData(BaseModel):
    semantic_pattern_id: str
    data_model_id: str
    register_id: str
    operation_id: str
    pattern_for_register: str
    pattern_for_operation: str

    class Config:
        from_attributes: bool = True


# IncomingTemplate Schemas
class IncomingTemplatePayload(BaseModel):
    template_id: Optional[str] = None
    register_id: str
    operation_id: str
    data_model_id: str
    template_file_id: str

    class Config:
        from_attributes: bool = True


class IncomingTemplateUpdatePayload(BaseModel):
    """Update payload for IncomingTemplate - only allows updating specific fields"""
    template_file_id: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingTemplateData(BaseModel):
    template_id: str
    register_id: str
    operation_id: str
    data_model_id: str
    template_file_id: str

    class Config:
        from_attributes: bool = True


# IncomingPayloadEnricher Schemas
class IncomingPayloadEnricherPayload(BaseModel):
    incoming_factory_id: Optional[str] = None
    data_model_id: str
    register_id: str
    operation_id: str
    raw_payload_enricher_class: str

    class Config:
        from_attributes: bool = True


class IncomingPayloadEnricherUpdatePayload(BaseModel):
    """Update payload for IncomingPayloadEnricher - only allows updating specific fields"""
    raw_payload_enricher_class: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingPayloadEnricherData(BaseModel):
    incoming_factory_id: str
    data_model_id: str
    register_id: str
    operation_id: str
    raw_payload_enricher_class: str

    class Config:
        from_attributes: bool = True


# DataModel Schemas
class DataModelPayload(BaseModel):
    data_model_id: Optional[str] = None
    data_model_mnemonic: str
    pattern_for_data_model: str
    is_active: bool = True

    class Config:
        from_attributes: bool = True


class DataModelUpdatePayload(BaseModel):
    """Update payload for DataModel - only allows updating specific fields"""
    data_model_mnemonic: Optional[str] = None
    pattern_for_data_model: Optional[str] = None

    class Config:
        from_attributes: bool = True


class DataModelData(BaseModel):
    data_model_id: str
    data_model_mnemonic: str
    pattern_for_data_model: str
    is_active: bool

    class Config:
        from_attributes: bool = True


# SubscriptionActivityLog Schemas
class SubscriptionActivityLogPayload(BaseModel):
    is_unsubscribe: bool = False
    description: Optional[str] = None
    partner_id: str
    subscription_url: str
    registry_callback_url: str
    header: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes: bool = True


class SubscriptionActivityLogData(BaseModel):
    subscription_activity_log_id: str
    is_unsubscribe: bool
    description: Optional[str] = None
    partner_id: str
    subscription_url: str
    registry_callback_url: str
    header: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    date_time: datetime

    class Config:
        from_attributes: bool = True

