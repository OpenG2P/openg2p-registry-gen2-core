
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class IngestionSummaryData(BaseModel):
    no_of_messages: int
    no_of_partners: int
    no_of_data_models: int


class IngestionDataSearchResultData(BaseModel):
    ingest_id: str
    partner_id: str
    partner_mnemonic: str
    data_model_id: str
    data_model_mnemonic: str
    ingest_message_id: str
    ingest_correlation_id: str
    receipt_date_time: datetime
    classification_status: str
    classification_date_time: Optional[datetime] = None
    classification_number_of_attempts: Optional[int] = None
    classification_latest_error_code: Optional[str] = None

    change_request_id: Optional[str] = None
    register_id: Optional[str] = None
    register_mnemonic: Optional[str] = None
    section_id: Optional[str] = None
    section_mnemonic: Optional[str] = None
    semantic_pattern_id: Optional[str] = None
    template_id: Optional[str] = None
    template_file_id: Optional[str] = None
    transformation_status: Optional[str] = None
    transformation_date_time: Optional[datetime] = None
    transformation_number_of_attempts: Optional[int] = None
    transformation_latest_error_code: Optional[str] = None
    ingestion_status: Optional[str] = None
    ingestion_date_time: Optional[datetime] = None
    ingestion_number_of_attempts: Optional[int] = None
    ingestion_latest_error_code: Optional[str] = None

class IngestionDataPayload(BaseModel):
    raw_data_json: Optional[dict] = None
    enriched_data_json: Optional[dict] = None
    transformed_data_json: Optional[dict] = None
