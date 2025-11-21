from pydantic import BaseModel
from datetime import date
from typing import Optional

from openg2p_registry_core.schemas import G2PRegisterSchema, G2PRegisterHistorySchema


class G2PRegisterSchemaFarmer(G2PRegisterSchema):

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    geo_administrative_area_small: Optional[str] = None
    geo_administrative_area_large: Optional[str] = None
    post_code: Optional[str] = None

class G2PRegisterHistorySchemaFarmer(G2PRegisterHistorySchema):
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    geo_administrative_area_small: Optional[str] = None
    geo_administrative_area_large: Optional[str] = None
    post_code: Optional[str] = None