from typing import Optional, List

from openg2p_fastapi_common.schemas import (
    G2PResponse,
    G2PResponseBody,
)
from .payload import (
    ChangeLogPayload, RegisterSummaryData, RegisterData, ChildRegisterData,
    SearchResultData, ChangeLogSearchResultData, IngestDataPayload,
    NumberOfVersionsData, NumberOfPendingChangeLogsData, ChangeLogData,
    ChangeLogsData, RecordData, VerificationData, VerificationsData,
    AddVerificationPayload, DeduplicationRegisterResultsData,
    DeduplicationChangelogResultsData
)


class ChangeLogResponseBody(G2PResponseBody):
    response_payload: Optional[ChangeLogPayload] = None

class ChangeLogResponse(G2PResponse):
    response_body: Optional[ChangeLogResponseBody] = None

# Register Summary Data
class RegisterSummaryDataResponseBody(G2PResponseBody):
    response_payload: Optional[List[RegisterSummaryData]] = None

class RegisterSummaryDataResponse(G2PResponse):
    response_body: Optional[RegisterSummaryDataResponseBody] = None


class AllRegistersResponseBody(G2PResponseBody):
    response_payload: Optional[List[RegisterData]] = None

class AllRegistersResponse(G2PResponse):
    response_body: Optional[AllRegistersResponseBody] = None


class ChildRegistersResponseBody(G2PResponseBody):
    response_payload: Optional[List[ChildRegisterData]] = None

class ChildRegistersResponse(G2PResponse):
    response_body: Optional[ChildRegistersResponseBody] = None


class SearchResultsResponseBody(G2PResponseBody):
    response_payload: Optional[List[SearchResultData]] = None

class SearchResultsResponse(G2PResponse):
    response_body: Optional[SearchResultsResponseBody] = None


class ChangeLogSearchResultsResponseBody(G2PResponseBody):
    response_payload: Optional[List[ChangeLogSearchResultData]] = None

class ChangeLogSearchResultsResponse(G2PResponse):
    response_body: Optional[ChangeLogSearchResultsResponseBody] = None

class IngestDataResponseBody(G2PResponseBody):
    response_payload: Optional[IngestDataPayload] = None

class IngestDataResponse(G2PResponse):
    response_body: Optional[IngestDataResponseBody] = None


class NumberOfVersionsResponseBody(G2PResponseBody):
    response_payload: Optional[NumberOfVersionsData] = None

class NumberOfVersionsResponse(G2PResponse):
    response_body: Optional[NumberOfVersionsResponseBody] = None


class NumberOfPendingChangeLogsResponseBody(G2PResponseBody):
    response_payload: Optional[NumberOfPendingChangeLogsData] = None

class NumberOfPendingChangeLogsResponse(G2PResponse):
    response_body: Optional[NumberOfPendingChangeLogsResponseBody] = None


class ChangeLogDataResponseBody(G2PResponseBody):
    response_payload: Optional[ChangeLogData] = None

class ChangeLogDataResponse(G2PResponse):
    response_body: Optional[ChangeLogDataResponseBody] = None


class ChangeLogsDataResponseBody(G2PResponseBody):
    response_payload: Optional[ChangeLogsData] = None

class ChangeLogsDataResponse(G2PResponse):
    response_body: Optional[ChangeLogsDataResponseBody] = None


class RecordDataResponseBody(G2PResponseBody):
    response_payload: Optional[RecordData] = None

class RecordDataResponse(G2PResponse):
    response_body: Optional[RecordDataResponseBody] = None


class VerificationsDataResponseBody(G2PResponseBody):
    response_payload: Optional[VerificationsData] = None

class VerificationsDataResponse(G2PResponse):
    response_body: Optional[VerificationsDataResponseBody] = None


class VerificationDataResponseBody(G2PResponseBody):
    response_payload: Optional[VerificationData] = None

class VerificationDataResponse(G2PResponse):
    response_body: Optional[VerificationDataResponseBody] = None


class DeduplicationRegisterResultsDataResponseBody(G2PResponseBody):
    response_payload: Optional[DeduplicationRegisterResultsData] = None

class DeduplicationRegisterResultsDataResponse(G2PResponse):
    response_body: Optional[DeduplicationRegisterResultsDataResponseBody] = None


class DeduplicationChangelogResultsDataResponseBody(G2PResponseBody):
    response_payload: Optional[DeduplicationChangelogResultsData] = None

class DeduplicationChangelogResultsDataResponse(G2PResponse):
    response_body: Optional[DeduplicationChangelogResultsDataResponseBody] = None
