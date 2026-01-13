
from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody
)
from pydantic import BaseModel

class EmptyRequestPayload(BaseModel):
    """Empty payload for requests that don't require any parameters"""
    pass
# Ingestion Summary
class GetIngestionSummaryDataRequestBody(G2PRequestBody):
    request_payload: EmptyRequestPayload

class GetIngestionSummaryDataRequest(G2PRequest):
    request_body: GetIngestionSummaryDataRequestBody

# Ingestion Search
class SearchIngestionDataRequestBody(G2PRequestBody):
    request_payload: EmptyRequestPayload

class SearchIngestionDataRequest(G2PRequest):
    request_body: SearchIngestionDataRequestBody

# Ingestion Data Payload
class GetIngestionDataRequestPayload(BaseModel):
    ingest_id: str

class GetIngestionDataPayloadRequestBody(G2PRequestBody):
    request_payload: GetIngestionDataRequestPayload

class GetIngestionDataPayloadRequest(G2PRequest):
    request_body: GetIngestionDataPayloadRequestBody