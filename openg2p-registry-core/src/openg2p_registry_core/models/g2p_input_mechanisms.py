import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_fastapi_common.models import BaseORMModel


class G2PInputMechanism(BaseORMModel):
    __tablename__ = "g2p_input_mechanisms"

    mechanism_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    register_id: Mapped[str] = mapped_column(String, nullable=False)
    mechanism_type: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    display_key: Mapped[str] = mapped_column(String, nullable=False)