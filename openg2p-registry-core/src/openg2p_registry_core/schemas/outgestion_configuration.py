from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class OutgoingTopicPayload(BaseModel):
    topic_id: Optional[str] = None
    register_id: Optional[str] = None
    data_model_id: Optional[str] = None
    websub_topic: Optional[str] = None
    description: Optional[str] = None
    # is_active: bool = True

    class Config:
        from_attributes = True

class OutgoingTopicUpdatePayload(BaseModel):
    topic_id: str
    register_id: Optional[str] = None
    data_model_id: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class OutgoingTopicData(BaseModel):
    topic_id: str
    register_id: str
    data_model_id: str
    websub_topic: str
    description: Optional[str] = None
    is_active: bool
    websub_publish_status: str
    websub_publish_datetime: Optional[datetime] = None
    websub_publish_number_of_attempts: int
    websub_publish_latest_error_message: Optional[str] = None

    class Config:
        from_attributes = True


class OutgoingTemplatePayload(BaseModel):
    template_id: Optional[str] = None
    data_model_id: Optional[str] = None
    register_id: Optional[str] = None
    template_file_id: Optional[str] = None

    class Config:
        from_attributes = True

class OutgoingTemplateUpdatePayload(BaseModel):
    template_id: str
    data_model_id: Optional[str] = None
    register_id: Optional[str] = None

class OutgoingTemplateData(BaseModel):
    template_id: str
    data_model_id: str
    register_id: str
    template_file_id: str

    class Config:
        from_attributes = True
