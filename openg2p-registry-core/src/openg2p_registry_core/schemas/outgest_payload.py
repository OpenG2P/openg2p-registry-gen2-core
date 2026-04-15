from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


# =============================================================================
# Outgest Data Schemas (response payloads)
# =============================================================================

class OutgoingTopicData(BaseModel):
    topic_id: str
    register_id: str
    register_mnemonic: Optional[str] = None
    data_model_id: str
    data_model_mnemonic: Optional[str] = None
    websub_topic: str
    description: Optional[str] = None
    is_active: bool
    websub_register_status: str
    websub_register_datetime: Optional[datetime] = None
    websub_register_number_of_attempts: int
    websub_register_latest_error_message: Optional[str] = Field(
        default=None, validation_alias="websub_register_latest_error_code"
    )

    class Config:
        from_attributes = True


class OutgoingTemplateData(BaseModel):
    template_id: str
    register_id: str
    register_mnemonic: Optional[str] = None
    data_model_id: str
    data_model_mnemonic: Optional[str] = None
    template_file_id: str

    class Config:
        from_attributes = True


# =============================================================================
# Outgest Request Payload Schemas
# =============================================================================

class OutgoingTopicPayload(BaseModel):
    topic_id: Optional[str] = None
    register_id: str
    data_model_id: str
    websub_topic: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class GetOutgoingTopicPayload(BaseModel):
    topic_id: str

    class Config:
        from_attributes = True


class OutgoingTopicUpdatePayload(BaseModel):
    topic_id: str
    register_id: Optional[str] = None
    data_model_id: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class OutgoingTemplatePayload(BaseModel):
    register_id: str
    data_model_id: str
    template_file_id: str

    class Config:
        from_attributes = True


class OutgoingTemplateUpdatePayload(BaseModel):
    template_id: str
    template_file_id: Optional[str] = None

    class Config:
        from_attributes = True


class GetOutgoingTemplatePayload(BaseModel):
    template_id: str

    class Config:
        from_attributes = True


class EmptyOutgestionRequestPayload(BaseModel):
    pass
