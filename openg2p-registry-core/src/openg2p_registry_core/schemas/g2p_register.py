from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class G2PRegisterSchema(BaseModel):

    internal_record_id: Optional[str] = None
    functional_record_id: Optional[str] = None
    link_internal_record_id: Optional[str] = None
    foundational_id: Optional[str] = None
    link_foundational_id: Optional[str] = None
    record_name: Optional[str] = None
    record_image_storage_id: Optional[str] = None
    administrative_area_large_id: Optional[str] = None
    administrative_area_small_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    last_approved_at: Optional[datetime] = None
    last_approved_by: Optional[str] = None
    