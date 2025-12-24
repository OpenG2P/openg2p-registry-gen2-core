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


class IncomingModelKeyPathPayload(BaseModel):
    key_path_id: Optional[str] = None
    keypath_for_message_id: str
    data_model_id: str
    key_path_for_sender: str
    key_path_for_signature: str
    key_path_for_signature_payload: str
    is_list: bool = False
    keypath_for_list_elements: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingModelKeyPathUpdatePayload(BaseModel):
    """Update payload for IncomingModelKeyPath - only allows updating specific fields"""
    key_path_id: str
    keypath_for_message_id: Optional[str] = None
    key_path_for_sender: Optional[str] = None
    key_path_for_signature: Optional[str] = None
    key_path_for_signature_payload: Optional[str] = None
    is_list: Optional[bool] = None
    keypath_for_list_elements: Optional[str] = None

    class Config:
        from_attributes: bool = True


# Individual edit payloads for IncomingModelKeyPath
class EditKeyPathForMessageIdPayload(BaseModel):
    """Edit payload for key_path_for_message_id field"""
    key_path_id: str
    keypath_for_message_id: str

    class Config:
        from_attributes: bool = True


class EditKeyPathForSenderPayload(BaseModel):
    """Edit payload for key_path_for_sender field"""
    key_path_id: str
    key_path_for_sender: str

    class Config:
        from_attributes: bool = True


class EditKeyPathForSignaturePayload(BaseModel):
    """Edit payload for key_path_for_signature field"""
    key_path_id: str
    key_path_for_signature: str

    class Config:
        from_attributes: bool = True


class EditKeyPathForSignaturePayloadPayload(BaseModel):
    """Edit payload for key_path_for_signature_payload field"""
    key_path_id: str
    key_path_for_signature_payload: str

    class Config:
        from_attributes: bool = True


class EditIsListPayload(BaseModel):
    """Edit payload for is_list field"""
    key_path_id: str
    is_list: bool

    class Config:
        from_attributes: bool = True


class EditKeyPathForListElementsPayload(BaseModel):
    """Edit payload for keypath_for_list_elements field"""
    key_path_id: str
    keypath_for_list_elements: str

    class Config:
        from_attributes: bool = True


class DeleteIncomingKeyPathPayload(BaseModel):
    """Delete payload for IncomingModelKeyPath"""
    key_path_id: str

    class Config:
        from_attributes: bool = True


class IncomingModelKeyPathData(BaseModel):
    key_path_id: str
    data_model_id: str
    keypath_for_message_id: str
    key_path_for_sender: str
    key_path_for_signature: str
    key_path_for_signature_payload: str
    is_list: bool
    keypath_for_list_elements: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingModelKeyPathListData(BaseModel):
    """Data for list API - includes data_model_mnemonic"""
    key_path_id: str
    data_model_id: str
    data_model_mnemonic: str
    is_list: bool

    class Config:
        from_attributes: bool = True


# IncomingModelSemanticPattern Schemas
class IncomingModelSemanticPatternPayload(BaseModel):
    semantic_pattern_id: Optional[str] = None
    data_model_id: str
    register_id: str
    section_id: str
    pattern_for_register: str
    pattern_for_section: str
    key_path_for_business_payload: str
    raw_payload_enricher_class: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingModelSemanticPatternUpdatePayload(BaseModel):
    """Update payload for IncomingModelSemanticPattern - only allows updating specific fields"""
    pattern_for_register: Optional[str] = None
    pattern_for_section: Optional[str] = None
    key_path_for_business_payload: Optional[str] = None
    raw_payload_enricher_class: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingModelSemanticPatternData(BaseModel):
    semantic_pattern_id: str
    data_model_id: str
    register_id: str
    section_id: str
    pattern_for_register: str
    pattern_for_section: str
    key_path_for_business_payload: str
    raw_payload_enricher_class: Optional[str] = None

    class Config:
        from_attributes: bool = True


# IncomingTemplate Schemas
class IncomingTemplatePayload(BaseModel):
    template_id: Optional[str] = None
    register_id: str
    data_model_id: str
    template_file_id: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingTemplateUpdatePayload(BaseModel):
    """Update payload for IncomingTemplate - only allows updating specific fields"""
    template_id: str
    template_file_id: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingTemplateData(BaseModel):
    template_id: str
    register_id: str
    data_model_id: str
    template_file_id: str

    class Config:
        from_attributes: bool = True


# DataModel Schemas
class DataModelPayload(BaseModel):
    data_model_id: Optional[str] = None
    data_model_mnemonic: str
    pattern_for_data_model: str
    response_template_file_id: Optional[str] = None
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
    response_template_file_id: str
    is_active: bool

    class Config:
        from_attributes: bool = True


class ChangeResponseTemplateFilePayload(BaseModel):
    """Payload for changing response template file of a DataModel"""
    data_model_id: str

    class Config:
        from_attributes: bool = True


class ChangeActiveStatusPayload(BaseModel):
    """Payload for changing active status of a DataModel"""
    data_model_id: str
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

