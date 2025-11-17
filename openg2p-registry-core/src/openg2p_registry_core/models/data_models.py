from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel

class DataModel(BaseORMModel):
    __tablename__ = "data_models"

    data_model_id: Mapped[str] = mapped_column(String, primary_key=True)
    data_model_mnemonic: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)