from typing import Optional, List

from openg2p_fastapi_common.schemas import G2PResponseBody, G2PResponse
from .payload_ingestion import IngestionSummaryData, IngestionDataSearchResultData, IngestionDataPayload

# Ingestion Summary Data
class IngestionSummaryDataResponseBody(G2PResponseBody):
    response_body: Optional[IngestionSummaryData] = None

class IngestionSummaryDataResponse(G2PResponse):
    response_body: Optional[IngestionSummaryDataResponseBody] = None

# Ingestion Search
class IngestionDataSearchResultsResponseBody(G2PResponseBody):
    response_payload: Optional[List[IngestionDataSearchResultData]] = None

class IngestionDataSearchResultsResponse(G2PResponse):
    response_body: Optional[IngestionDataSearchResultsResponseBody] = None

# Ingestion Data Payload
class IngestionDataPayloadResponseBody(G2PResponseBody):
    response_payload: Optional[IngestionDataPayload] = None

class IngestionDataPayloadResponse(G2PResponse):
    response_body: Optional[IngestionDataPayloadResponseBody] = None
