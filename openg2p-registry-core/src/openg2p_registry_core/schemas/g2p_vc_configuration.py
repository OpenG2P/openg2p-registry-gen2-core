from typing import Optional, List
from pydantic import BaseModel
from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PResponse,
    G2PResponseBody,
    G2PResponseHeader,
)


# Data Payloads
class VcConfigurationData(BaseModel):
    vc_config_id: str
    register_id: str
    vc_mnemonic: str
    descriptor_schema: dict

    class Config:
        from_attributes: bool = True


# Request Payloads
class VcConfigurationRequestPayload(BaseModel):
    vc_config_id: Optional[str] = None
    register_id: Optional[str] = None
    vc_mnemonic: Optional[str] = None
    descriptor_schema: Optional[dict] = None


class VcConfigurationRequestBody(G2PRequestBody):
    request_payload: VcConfigurationRequestPayload


class VcConfigurationRequest(G2PRequest):
    request_body: VcConfigurationRequestBody


# Response Payloads
class VcConfigurationResponseBody(G2PResponseBody):
    response_payload: Optional[List[VcConfigurationData]] = None


class VcConfigurationResponse(G2PResponse):
    response_body: Optional[VcConfigurationResponseBody] = None

