import enum
from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel

class ProcessStatusEnum(enum.Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"         # COMPLETED
    FAILED = "FAILED"

class IncomingRawData(BaseORMModel):

    __tablename__ = "incoming_raw_data"

    ingest_id: Mapped[str] = mapped_column(String, primary_key=True)
    partner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    data_model_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    receipt_date_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    classification_status: Mapped[str] = mapped_column(String, nullable=False, index=True, default=ProcessStatusEnum.PENDING.value)
    classification_date_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

class IncomingRawDataPayload(BaseORMModel):

    __tablename__ = "incoming_raw_data_payloads"

    ingest_id: Mapped[str] = mapped_column(String, nullable=False, index=True, primary_key=True)
    raw_data_json: Mapped[JSON] = mapped_column(JSON, nullable=True)
    raw_data_xml: Mapped[Text] = mapped_column(Text, nullable=True)

class IncomingEnrichedTransformedData(BaseORMModel):
    __tablename__ = "incoming_enriched_transformed_data"

    ingest_id: Mapped[str] = mapped_column(String, nullable=False, index=True, primary_key=True)
    enriched_data_json: Mapped[JSON] = mapped_column(JSON, nullable=True)
    enriched_data_xml: Mapped[Text] = mapped_column(Text, nullable=True)
    transformed_data_json: Mapped[JSON] = mapped_column(JSON, nullable=True)
    transformed_data_xml: Mapped[Text] = mapped_column(Text, nullable=True)

class IncomingClassifiedData(BaseORMModel):

    __tablename__ = "incoming_classified_data"

    ingest_id: Mapped[str] = mapped_column(String, nullable=False, index=True, primary_key=True)
    data_model_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    operation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    classified_date_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    transformation_status: Mapped[str] = mapped_column(String, nullable=False, index=True, default=ProcessStatusEnum.PENDING.value)
    transformation_date_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    ingestion_status: Mapped[str] = mapped_column(String, nullable=False, index=True, default=ProcessStatusEnum.NOT_APPLICABLE.value)
    ingestion_date_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
