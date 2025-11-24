from typing import Optional
from pydantic import BaseModel


class IncomingPartnerPayload(BaseModel):
    partner_id: Optional[str] = None
    partner_mnemonic: str
    keymanager_reference_id: str
    is_active: bool = True

    class Config:
        from_attributes: bool = True


class IncomingPartnerUpdatePayload(BaseModel):
    """Update payload for IncomingPartner - only allows updating specific fields"""
    partner_mnemonic: Optional[str] = None
    keymanager_reference_id: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes: bool = True


class IncomingPartnerData(BaseModel):
    partner_id: str
    partner_mnemonic: str
    keymanager_reference_id: str
    is_active: bool

    class Config:
        from_attributes: bool = True


class IncomingModelSignaturePatternPayload(BaseModel):
    signature_pattern_id: Optional[str] = None
    data_model_id: str
    pattern_for_sender: str
    pattern_for_signature: str

    class Config:
        from_attributes: bool = True


class IncomingModelSignaturePatternUpdatePayload(BaseModel):
    """Update payload for IncomingModelSignaturePattern - only allows updating specific fields"""
    pattern_for_sender: Optional[str] = None
    pattern_for_signature: Optional[str] = None

    class Config:
        from_attributes: bool = True


class IncomingModelSignaturePatternData(BaseModel):
    signature_pattern_id: str
    data_model_id: str
    pattern_for_sender: str
    pattern_for_signature: str

    class Config:
        from_attributes: bool = True

