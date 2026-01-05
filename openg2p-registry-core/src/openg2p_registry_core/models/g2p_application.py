from enum import unique, Enum
import json
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Index
from sqlalchemy.orm import validates
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy.dialects.postgresql import JSONB


class ApplicationStatusEnum(Enum):
    DRAFT = "DRAFT"
    FINAL = "FINAL"

class ChangeRequestStatusEnum(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
   
class G2PApplication(BaseORMModel):
    
    application_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    application_status: Mapped[ApplicationStatusEnum] = mapped_column(String, nullable=False, default=ApplicationStatusEnum.DRAFT.value)
    change_request_submission_status: Mapped[ChangeRequestStatusEnum] = mapped_column(String, nullable=False, default=ChangeRequestStatusEnum.PENDING.value)
    change_request_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    submission_no_of_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    submission_latest_datetime: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    submission_latest_error_code: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    last_updated_by: Mapped[str] = mapped_column(String, nullable=False)
    last_updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

class G2PApplicationSectionPayload(BaseORMModel):
    application_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    section_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    application_payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    application_json_text: Mapped[str] = mapped_column(Text, nullable=False)

    @validates('application_payload_json')
    def update_application_json_text(self, key, value):
        """Automatically populate application_json_text from application_payload_json JSON"""
        if value:
            # Convert JSON to string representation for searching
            if isinstance(value, dict):
                self.application_json_text = json.dumps(value)
            else:
                self.application_json_text = str(value)
        return value
    
    __table_args__ = (
        Index('ix_g2p_application_section_payloads_application_json_text_gin', 'application_json_text', postgresql_using='gin', postgresql_ops={'application_json_text': 'gin_trgm_ops'}),
    )
