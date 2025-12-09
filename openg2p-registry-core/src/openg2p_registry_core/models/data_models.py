import enum
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel

class DataModel(BaseORMModel):
    __tablename__ = "data_models"

    data_model_id: Mapped[str] = mapped_column(String, primary_key=True)
    data_model_mnemonic: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    pattern_for_data_model: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class ProcessStatusEnum(enum.Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"         # COMPLETED
    FAILED = "FAILED"
