from enum import unique
from operator import index
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Date
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegisterFarmerBase(BaseORMModel):
    __abstract__ = True
    
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[str] = mapped_column(Date, nullable=False)
    address_line_1: Mapped[str] = mapped_column(String, nullable=False)
    address_line_2: Mapped[str] = mapped_column(String, nullable=True)
    geo_administrative_area_small: Mapped[str] = mapped_column(String, nullable=False)
    geo_administrative_area_large: Mapped[str] = mapped_column(String, nullable=False)
    post_code: Mapped[str] = mapped_column(String, nullable=False)

# All Register classes should have the prefix G2PRegister
class G2PRegisterFarmer(G2PRegisterFarmerBase, G2PRegister):
    __tablename__ = "g2p_register_farmers"
    pass

# All Register History classes should have the prefix G2PRegisterHistory
class G2PRegisterHistoryFarmer(G2PRegisterFarmerBase, G2PRegisterHistory):
    __tablename__ = "g2p_register_history_farmers"
    pass
