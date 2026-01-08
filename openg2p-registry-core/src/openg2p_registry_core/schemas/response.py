from typing import Optional, List

from openg2p_fastapi_common.schemas import (
    G2PResponse,
    G2PResponseBody,
)
from .payload import (
    ChangeRequestResponsePayload, RegisterSummaryData, ChangeRequestSummaryData, RegisterData, ChildRegisterData,
    RegisterUITabData, SearchResultData, ChangeRequestSearchResultData, IngestDataPayload,
    NumberOfVersionsData, NumberOfPendingChangeRequestsData, NumberOfCrossRegisterChangesData,
    CrossRegisterChangeRequestData, CrossRegisterChangesData,
    ChangeRequestData, ChangeRequestsData, ChangeRequestFlattenedData, RecordData, VerificationData, VerificationsData,
    AddVerificationPayload, DeduplicationRegisterResultsData,
    DeduplicationChangerequestResultsData, RegisterSchemaData, RegisterSectionData,
    RegisterTabRecordData, UploadDocumentsResponseData, UploadRecordImageData,
    RegistryConfigurationData, NumberOfRequestsPendingData, EarliestPendingChangeRequestData,
    DocumentLabelsForSectionData, SectionDocumentsData, ChangeRequestDocumentsData,
    RecordHistoryData, RecordHistoryListData
)


class ChangeRequestResponseBody(G2PResponseBody):
    response_payload: Optional[ChangeRequestResponsePayload] = None

class ChangeRequestResponse(G2PResponse):
    response_body: Optional[ChangeRequestResponseBody] = None

# Register Summary Data
class RegisterSummaryDataResponseBody(G2PResponseBody):
    response_payload: Optional[List[RegisterSummaryData]] = None

class RegisterSummaryDataResponse(G2PResponse):
    response_body: Optional[RegisterSummaryDataResponseBody] = None


# ChangeRequest Summary Data
class ChangeRequestSummaryDataResponseBody(G2PResponseBody):
    response_payload: Optional[ChangeRequestSummaryData] = None

class ChangeRequestSummaryDataResponse(G2PResponse):
    response_body: Optional[ChangeRequestSummaryDataResponseBody] = None


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


class ChangeRequestSearchResultsResponseBody(G2PResponseBody):
    response_payload: Optional[List[ChangeRequestSearchResultData]] = None

class ChangeRequestSearchResultsResponse(G2PResponse):
    response_body: Optional[ChangeRequestSearchResultsResponseBody] = None

class IngestDataResponseBody(G2PResponseBody):
    response_payload: Optional[IngestDataPayload] = None

class IngestDataResponse(G2PResponse):
    response_body: Optional[IngestDataResponseBody] = None


class NumberOfVersionsResponseBody(G2PResponseBody):
    response_payload: Optional[NumberOfVersionsData] = None

class NumberOfVersionsResponse(G2PResponse):
    response_body: Optional[NumberOfVersionsResponseBody] = None


class RecordHistoryDataResponseBody(G2PResponseBody):
    response_payload: Optional["RecordHistoryListData"] = None

class RecordHistoryDataResponse(G2PResponse):
    response_body: Optional[RecordHistoryDataResponseBody] = None


class NumberOfPendingChangeRequestsResponseBody(G2PResponseBody):
    response_payload: Optional[NumberOfPendingChangeRequestsData] = None

class NumberOfPendingChangeRequestsResponse(G2PResponse):
    response_body: Optional[NumberOfPendingChangeRequestsResponseBody] = None


class NumberOfCrossRegisterChangesResponseBody(G2PResponseBody):
    response_payload: Optional[NumberOfCrossRegisterChangesData] = None


class NumberOfCrossRegisterChangesResponse(G2PResponse):
    response_body: Optional[NumberOfCrossRegisterChangesResponseBody] = None


class CrossRegisterChangesDataResponseBody(G2PResponseBody):
    response_payload: Optional[CrossRegisterChangesData] = None


class CrossRegisterChangesDataResponse(G2PResponse):
    response_body: Optional[CrossRegisterChangesDataResponseBody] = None


class ChangeRequestDataResponseBody(G2PResponseBody):
    response_payload: Optional[ChangeRequestData] = None

class ChangeRequestDataResponse(G2PResponse):
    response_body: Optional[ChangeRequestDataResponseBody] = None


class ChangeRequestsDataResponseBody(G2PResponseBody):
    response_payload: Optional[ChangeRequestsData] = None

class ChangeRequestsDataResponse(G2PResponse):
    response_body: Optional[ChangeRequestsDataResponseBody] = None


class ChangeRequestFlattenedDataResponseBody(G2PResponseBody):
    response_payload: Optional[List[ChangeRequestFlattenedData]] = None

class ChangeRequestFlattenedDataResponse(G2PResponse):
    response_body: Optional[ChangeRequestFlattenedDataResponseBody] = None


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


class DeduplicationChangerequestResultsDataResponseBody(G2PResponseBody):
    response_payload: Optional[DeduplicationChangerequestResultsData] = None

class DeduplicationChangerequestResultsDataResponse(G2PResponse):
    response_body: Optional[DeduplicationChangerequestResultsDataResponseBody] = None


class RegisterSchemaDataResponseBody(G2PResponseBody):
    response_payload: Optional[RegisterSchemaData] = None


class RegisterSchemaDataResponse(G2PResponse):
    response_body: Optional[RegisterSchemaDataResponseBody] = None


class RegisterDataResponseBody(G2PResponseBody):
    response_payload: Optional[RegisterData] = None


class RegisterDataResponse(G2PResponse):
    response_body: Optional[RegisterDataResponseBody] = None


class RegisterSectionsDataResponseBody(G2PResponseBody):
    response_payload: Optional[List[RegisterSectionData]] = None


class RegisterSectionsDataResponse(G2PResponse):
    response_body: Optional[RegisterSectionsDataResponseBody] = None


class RegisterSectionDataResponseBody(G2PResponseBody):
    response_payload: Optional[RegisterSectionData] = None


class RegisterSectionDataResponse(G2PResponse):
    response_body: Optional[RegisterSectionDataResponseBody] = None


class RegisterTabsDataResponseBody(G2PResponseBody):
    response_payload: Optional[List[RegisterUITabData]] = None


class RegisterTabsDataResponse(G2PResponse):
    response_body: Optional[RegisterTabsDataResponseBody] = None


class RegisterTabDataResponseBody(G2PResponseBody):
    response_payload: Optional[RegisterUITabData] = None


class RegisterTabDataResponse(G2PResponse):
    response_body: Optional[RegisterTabDataResponseBody] = None


class SectionRecordsDataResponseBody(G2PResponseBody):
    response_payload: Optional[List[RecordData]] = None


class SectionRecordsDataResponse(G2PResponse):
    response_body: Optional[SectionRecordsDataResponseBody] = None


class RegisterTabRecordsDataResponseBody(G2PResponseBody):
    response_payload: Optional[List[RegisterTabRecordData]] = None


class RegisterTabRecordsDataResponse(G2PResponse):
    response_body: Optional[RegisterTabRecordsDataResponseBody] = None


# Upload Documents Response
class UploadDocumentsResponseBody(G2PResponseBody):
    response_payload: Optional[UploadDocumentsResponseData] = None


class UploadDocumentsResponse(G2PResponse):
    response_body: Optional[UploadDocumentsResponseBody] = None


# Upload Record Image Response
class UploadRecordImageResponseBody(G2PResponseBody):
    response_payload: Optional["UploadRecordImageData"] = None


class UploadRecordImageResponse(G2PResponse):
    response_body: Optional[UploadRecordImageResponseBody] = None


# Document Labels and Section Documents Responses
class DocumentLabelsForSectionResponseBody(G2PResponseBody):
    response_payload: Optional["DocumentLabelsForSectionData"] = None


class DocumentLabelsForSectionResponse(G2PResponse):
    response_body: Optional[DocumentLabelsForSectionResponseBody] = None


class SectionDocumentsResponseBody(G2PResponseBody):
    response_payload: Optional["SectionDocumentsData"] = None


class SectionDocumentsResponse(G2PResponse):
    response_body: Optional[SectionDocumentsResponseBody] = None


class ChangeRequestDocumentsResponseBody(G2PResponseBody):
    response_payload: Optional["ChangeRequestDocumentsData"] = None


class ChangeRequestDocumentsResponse(G2PResponse):
    response_body: Optional[ChangeRequestDocumentsResponseBody] = None


# =============================================================================
# Registry Configuration Responses
# =============================================================================

class RegistryConfigurationDataResponseBody(G2PResponseBody):
    response_payload: Optional["RegistryConfigurationData"] = None


class RegistryConfigurationDataResponse(G2PResponse):
    response_body: Optional[RegistryConfigurationDataResponseBody] = None


# =============================================================================
# Change Request Additional Responses
# =============================================================================

class NumberOfRequestsPendingResponseBody(G2PResponseBody):
    response_payload: Optional["NumberOfRequestsPendingData"] = None


class NumberOfRequestsPendingResponse(G2PResponse):
    response_body: Optional[NumberOfRequestsPendingResponseBody] = None


class EarliestPendingChangeRequestResponseBody(G2PResponseBody):
    response_payload: Optional["EarliestPendingChangeRequestData"] = None


class EarliestPendingChangeRequestResponse(G2PResponse):
    response_body: Optional[EarliestPendingChangeRequestResponseBody] = None
