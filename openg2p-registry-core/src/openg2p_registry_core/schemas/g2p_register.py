from pydantic import BaseModel
from datetime import date
from typing import Optional

class G2PRegisterSchema(BaseModel):
    
    internal_record_id: Optional[str] = None
    functional_record_id: Optional[str] = None
    link_record_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[date] = None
    last_approved_at: Optional[date] = None
    last_approved_by: Optional[str] = None
    