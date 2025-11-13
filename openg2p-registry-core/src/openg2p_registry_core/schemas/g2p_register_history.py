from pydantic import BaseModel
from datetime import date
from typing import Optional

class G2PRegisterHistorySchema(BaseModel):
    
    history_record_id: Optional[str] = None
    internal_record_id: Optional[str] = None
    change_log_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[date] = None
    approved_by: Optional[str] = None
    approved_at: Optional[date] = None
    