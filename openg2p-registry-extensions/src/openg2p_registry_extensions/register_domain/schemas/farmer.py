from pydantic import BaseModel
from datetime import date
from typing import Optional

from openg2p_registry_core.schemas import G2PRegisterSchema, G2PRegisterHistorySchema


class G2PRegisterSchemaFarmer(G2PRegisterSchema):

    first_name: str
    last_name: str
    date_of_birth: date
    address_line_1: str
    address_line_2: Optional[str] = None
    geo_administrative_area_small: str
    geo_administrative_area_large: str
    post_code: str

class G2PRegisterHistorySchemaFarmer(G2PRegisterHistorySchema):
    
    first_name: str
    last_name: str
    date_of_birth: date
    address_line_1: str
    address_line_2: Optional[str] = None
    geo_administrative_area_small: str
    geo_administrative_area_large: str
    post_code: str