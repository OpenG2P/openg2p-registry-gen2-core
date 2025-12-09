from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel

from .data_models import ProcessStatusEnum

class OutgoingRawData(BaseORMModel):
    
    __tablename__ = "outgoing_raw_data"
    
    outgest_id: Mapped[str] = mapped_column(String, primary_key=True)
    change_log_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    internal_record_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    data_model_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    topic_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=datetime.now())
    
    changed_by: Mapped[str] = mapped_column(String, nullable=False)
    changed_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    approved_by: Mapped[str] = mapped_column(String, nullable=True)
    approved_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    changed_by_partner_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    
    transformation_status: Mapped[str] = mapped_column(String, nullable=False, index=True, default=ProcessStatusEnum.PENDING.value)
    transformation_datetime: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    transformation_latest_error_code: Mapped[str] = mapped_column(String, nullable=True)
    transformation_number_of_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    publish_status: Mapped[str] = mapped_column(String, nullable=False, index=True, default=ProcessStatusEnum.PENDING.value)
    publish_datetime: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    publish_latest_error_code: Mapped[str] = mapped_column(String, nullable=True)
    publish_number_of_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

class OutgoingRawDataPayload(BaseORMModel):
    
    __tablename__ = "outgoing_raw_data_payloads"
    
    change_log_id: Mapped[str] = mapped_column(String, nullable=False, index=True, primary_key=True)
    raw_data_json: Mapped[JSONB] = mapped_column(JSONB, nullable=True)
    raw_data_xml: Mapped[Text] = mapped_column(Text, nullable=True)

class OutgoingTransformedDataPayload(BaseORMModel):
    
    __tablename__ = "outgoing_transformed_data_payloads"
    
    change_log_id: Mapped[str] = mapped_column(String, nullable=False, index=True, primary_key=True)
    transformed_data_json: Mapped[JSONB] = mapped_column(JSONB, nullable=True)
    transformed_data_xml: Mapped[Text] = mapped_column(Text, nullable=True)