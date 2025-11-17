import enum
from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel

class ProcessStatusEnum(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class IncomingRawData(BaseORMModel):

    __tablename__ = "incoming_raw_data"

    ingest_id: Mapped[str] = mapped_column(String, primary_key=True)
    partner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    data_model_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    receipt_date_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    process_status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    process_date_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

class IncomingRawDataPayload(BaseORMModel):

    __tablename__ = "incoming_raw_data_payloads"

    ingest_id: Mapped[str] = mapped_column(String, nullable=False, index=True, primary_key=True)
    raw_data_json: Mapped[JSON] = mapped_column(JSON, nullable=False)
    raw_data_xml: Mapped[Text] = mapped_column(Text, nullable=True)

class IncomingClassifiedData(BaseORMModel):

    __tablename__ = "incoming_classified_data"

    ingest_id: Mapped[str] = mapped_column(String, nullable=False, index=True, primary_key=True)
    inbound_register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    inbound_operation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    classified_date_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    process_status: Mapped[str] = mapped_column(String, nullable=False, index=True, default=ProcessStatusEnum.PENDING.value)
    process_date_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    sender_processor_class: Mapped[str] = mapped_column(String, nullable=False)