from datetime import datetime
from typing import List
from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.schemas import G2PRequest, G2PResponse, G2PResponseHeader, G2PResponseStatus, G2PResponseBody, G2PPaginationResponse
from openg2p_registry_core.schemas import (
    ChangeLogResponsePayload, ChangeLogResponse, ChangeLogResponseBody,
    RegisterSummaryData, RegisterSummaryDataResponse, RegisterSummaryDataResponseBody,
    ChangeLogSummaryData, ChangeLogSummaryDataResponse, ChangeLogSummaryDataResponseBody,
    RegisterData, AllRegistersResponse, AllRegistersResponseBody,
    RegisterDataResponse, RegisterDataResponseBody,
    ChildRegisterData, ChildRegistersResponse, ChildRegistersResponseBody,
    SearchResultData, SearchResultsResponse, SearchResultsResponseBody,
    ChangeLogSearchResultData, ChangeLogSearchResultsResponse, ChangeLogSearchResultsResponseBody,
    NumberOfVersionsData, NumberOfVersionsResponse, NumberOfVersionsResponseBody,
    NumberOfPendingChangeLogsData, NumberOfPendingChangeLogsResponse, NumberOfPendingChangeLogsResponseBody,
    NumberOfCrossRegisterChangesData, NumberOfCrossRegisterChangesResponse, NumberOfCrossRegisterChangesResponseBody,
    CrossRegisterChangeLogData, CrossRegisterChangesData, CrossRegisterChangesDataResponse, CrossRegisterChangesDataResponseBody,
    ChangeLogData, ChangeLogDataResponse, ChangeLogDataResponseBody,
    ChangeLogsData, ChangeLogsDataResponse, ChangeLogsDataResponseBody,
    RecordData, RecordDataResponse, RecordDataResponseBody,
    VerificationsData, VerificationsDataResponse, VerificationsDataResponseBody,
    VerificationData, VerificationDataResponse, VerificationDataResponseBody,
    DeduplicationRegisterResultsData, DeduplicationRegisterResultsDataResponse, DeduplicationRegisterResultsDataResponseBody,
    DeduplicationChangelogResultsData, DeduplicationChangelogResultsDataResponse, DeduplicationChangelogResultsDataResponseBody,
    IncomingPartnerData, IncomingPartnerResponseBody,
    IncomingModelKeyPathData, IncomingModelKeyPathResponseBody,
    IncomingModelSemanticPatternResponseBody, IncomingTemplateResponseBody,
    DataModelResponseBody, OutgoingTopicResponseBody, OutgoingTemplateResponseBody,
    RegisterSchemaData, RegisterSchemaDataResponse, RegisterSchemaDataResponseBody,
    RegisterSectionData, RegisterSectionsDataResponse, RegisterSectionsDataResponseBody,
    RegisterSectionDataResponse, RegisterSectionDataResponseBody,
    RegisterUITabData, RegisterTabsDataResponse, RegisterTabsDataResponseBody,
    RegisterTabDataResponse, RegisterTabDataResponseBody,
    SectionRecordsDataResponse, SectionRecordsDataResponseBody,
)
from openg2p_registry_core.errors import G2PRegistryException


class RequestResponseHelper(BaseService):

    def construct_all_registers_success_response(self, all_registers_list: List[RegisterData], g2p_request: G2PRequest = None) -> AllRegistersResponse:
        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: AllRegistersResponseBody = AllRegistersResponseBody(
            response_payload=all_registers_list
        )

        all_registers_response: AllRegistersResponse = AllRegistersResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return all_registers_response
    
    def construct_error_response(self, error: Exception, g2p_request: G2PRequest = None) -> G2PResponse:
        """
        Unified error response constructor that handles both G2PRegistryException and generic exceptions.
        For G2PRegistryException, uses the exception's code and message.
        For other exceptions, uses error code "500" and the exception message.
        g2p_request is optional - if not provided, request_id will be empty string.
        """
        if isinstance(error, G2PRegistryException):
            error_code = error.code
            error_message = error.message
        else:
            error_code = "500"
            error_message = str(error)

        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.ERROR,
            response_error_code=error_code,
            response_error_message=error_message,
            response_timestamp=datetime.now()
        )
        error_response = G2PResponse(
            response_header=g2p_response_header,
            response_body=G2PResponseBody(
                pagination_response=None,
                response_payload=None
            )
        )

        return error_response
