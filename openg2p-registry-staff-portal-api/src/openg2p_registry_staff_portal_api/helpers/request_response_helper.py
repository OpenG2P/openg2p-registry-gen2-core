from datetime import datetime
from typing import List
from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.schemas import G2PRequest, G2PResponse, G2PResponseHeader, G2PResponseStatus, G2PResponseBody, G2PPaginationResponse
from openg2p_registry_core.schemas import (
    ChangeRequestResponsePayload, ChangeRequestResponse, ChangeRequestResponseBody,
    RegisterSummaryData, RegisterSummaryDataResponse, RegisterSummaryDataResponseBody,
    ChangeRequestSummaryData, ChangeRequestSummaryDataResponse, ChangeRequestSummaryDataResponseBody,
    RegisterData, AllRegistersResponse, AllRegistersResponseBody,
    RegisterDataResponse, RegisterDataResponseBody,
    ChildRegisterData, ChildRegistersResponse, ChildRegistersResponseBody,
    SearchResultData, SearchResultsResponse, SearchResultsResponseBody,
    ChangeRequestSearchResultData, ChangeRequestSearchResultsResponse, ChangeRequestSearchResultsResponseBody,
    NumberOfVersionsData, NumberOfVersionsResponse, NumberOfVersionsResponseBody,
    NumberOfPendingChangeRequestsData, NumberOfPendingChangeRequestsResponse, NumberOfPendingChangeRequestsResponseBody,
    NumberOfCrossRegisterChangesData, NumberOfCrossRegisterChangesResponse, NumberOfCrossRegisterChangesResponseBody,
    CrossRegisterChangeRequestData, CrossRegisterChangesData, CrossRegisterChangesDataResponse, CrossRegisterChangesDataResponseBody,
    ChangeRequestData, ChangeRequestDataResponse, ChangeRequestDataResponseBody,
    ChangeRequestsData,
    ChangeRequestFlattenedData, ChangeRequestFlattenedDataResponse, ChangeRequestFlattenedDataResponseBody,
    RecordData, RecordDataResponse, RecordDataResponseBody,
    VerificationsData, VerificationsDataResponse, VerificationsDataResponseBody,
    VerificationData, VerificationDataResponse, VerificationDataResponseBody,
    DeduplicationRegisterResultsData, DeduplicationRegisterResultsDataResponse, DeduplicationRegisterResultsDataResponseBody,
    DeduplicationChangerequestResultsData, DeduplicationChangerequestResultsDataResponse, DeduplicationChangerequestResultsDataResponseBody,
    IncomingPartnerData, IncomingPartnerResponseBody, IncomingPartnersResponseBody,
    IncomingModelKeyPathData, IncomingModelKeyPathResponseBody, IncomingModelKeyPathListResponseBody,
    IncomingModelSemanticPatternResponseBody, IncomingTemplateResponseBody,
    DataModelResponseBody, DataModelsResponseBody, SubscriptionActivityLogsResponseBody,
    OutgoingTopicResponseBody, OutgoingTemplateResponseBody,
    RegisterSchemaData, RegisterSchemaDataResponse, RegisterSchemaDataResponseBody,
    RegisterSectionData, RegisterSectionsDataResponse, RegisterSectionsDataResponseBody,
    RegisterSectionDataResponse, RegisterSectionDataResponseBody,
    RegisterUITabData, RegisterTabsDataResponse, RegisterTabsDataResponseBody,
    RegisterTabDataResponse, RegisterTabDataResponseBody,
    SectionRecordsDataResponse, SectionRecordsDataResponseBody,
    RegisterTabRecordData, RegisterTabRecordsDataResponse, RegisterTabRecordsDataResponseBody,
    UploadDocumentsResponseData, UploadDocumentsResponse, UploadDocumentsResponseBody,
    RegistryConfigurationData, RegistryConfigurationDataResponse, RegistryConfigurationDataResponseBody,
    NumberOfRequestsPendingData, NumberOfRequestsPendingResponse, NumberOfRequestsPendingResponseBody,
    EarliestPendingChangeRequestData, EarliestPendingChangeRequestResponse, EarliestPendingChangeRequestResponseBody,
)
from openg2p_registry_core.errors import G2PRegistryException


class RequestResponseHelper(BaseService):
    def construct_change_request_success_response(self, change_request_response_payload: ChangeRequestResponsePayload, g2p_request: G2PRequest) -> ChangeRequestResponse:

        g2p_response_header = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: ChangeRequestResponseBody = ChangeRequestResponseBody(
            response_payload=change_request_response_payload
        )

        change_request_response: ChangeRequestResponse = ChangeRequestResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return change_request_response
    
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

    def construct_register_summary_data_success_response(self, register_summary_data_list: List[RegisterSummaryData], g2p_request: G2PRequest = None) -> RegisterSummaryDataResponse:
        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RegisterSummaryDataResponseBody = RegisterSummaryDataResponseBody(
            response_payload=register_summary_data_list
        )

        register_summary_data_response: RegisterSummaryDataResponse = RegisterSummaryDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return register_summary_data_response

    def construct_changerequest_summary_data_success_response(self, changerequest_summary_data: ChangeRequestSummaryData, g2p_request: G2PRequest = None) -> ChangeRequestSummaryDataResponse:
        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: ChangeRequestSummaryDataResponseBody = ChangeRequestSummaryDataResponseBody(
            response_payload=changerequest_summary_data
        )

        changerequest_summary_data_response: ChangeRequestSummaryDataResponse = ChangeRequestSummaryDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return changerequest_summary_data_response

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

    def construct_child_registers_success_response(self, child_registers_list: List[ChildRegisterData], g2p_request: G2PRequest = None) -> ChildRegistersResponse:
        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: ChildRegistersResponseBody = ChildRegistersResponseBody(
            response_payload=child_registers_list
        )

        child_registers_response: ChildRegistersResponse = ChildRegistersResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return child_registers_response

    def construct_search_results_success_response(self, search_results_list: List[SearchResultData], g2p_request: G2PRequest = None, number_of_items: int = 0, number_of_pages: int = 0) -> SearchResultsResponse:
        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        pagination_response = None
        if number_of_items > 0 or number_of_pages > 0:
            pagination_response = G2PPaginationResponse(
                number_of_items=number_of_items,
                number_of_pages=number_of_pages
            )

        response_body: SearchResultsResponseBody = SearchResultsResponseBody(
            pagination_response=pagination_response,
            response_payload=search_results_list
        )

        search_results_response: SearchResultsResponse = SearchResultsResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return search_results_response

    def construct_change_request_search_results_success_response(self, search_results_list: List[ChangeRequestSearchResultData], g2p_request: G2PRequest = None, number_of_items: int = None, number_of_pages: int = None) -> ChangeRequestSearchResultsResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        pagination_response = None
        if number_of_items is not None and number_of_pages is not None:
            pagination_response = G2PPaginationResponse(
                number_of_items=number_of_items,
                number_of_pages=number_of_pages
            )

        response_body: ChangeRequestSearchResultsResponseBody = ChangeRequestSearchResultsResponseBody(
            response_payload=search_results_list,
            pagination_response=pagination_response
        )

        change_request_search_results_response: ChangeRequestSearchResultsResponse = ChangeRequestSearchResultsResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return change_request_search_results_response

    def construct_number_of_versions_success_response(self, number_of_versions_data: NumberOfVersionsData, g2p_request: G2PRequest = None) -> NumberOfVersionsResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: NumberOfVersionsResponseBody = NumberOfVersionsResponseBody(
            response_payload=number_of_versions_data
        )

        number_of_versions_response: NumberOfVersionsResponse = NumberOfVersionsResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return number_of_versions_response

    def construct_number_of_pending_change_requests_success_response(self, number_of_pending_change_requests_data: NumberOfPendingChangeRequestsData, g2p_request: G2PRequest = None) -> NumberOfPendingChangeRequestsResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: NumberOfPendingChangeRequestsResponseBody = NumberOfPendingChangeRequestsResponseBody(
            response_payload=number_of_pending_change_requests_data
        )

        number_of_pending_change_requests_response: NumberOfPendingChangeRequestsResponse = NumberOfPendingChangeRequestsResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return number_of_pending_change_requests_response

    def construct_number_of_cross_register_changes_success_response(self, number_of_cross_register_changes_data: NumberOfCrossRegisterChangesData, g2p_request: G2PRequest = None) -> NumberOfCrossRegisterChangesResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: NumberOfCrossRegisterChangesResponseBody = NumberOfCrossRegisterChangesResponseBody(
            response_payload=number_of_cross_register_changes_data
        )

        number_of_cross_register_changes_response: NumberOfCrossRegisterChangesResponse = NumberOfCrossRegisterChangesResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return number_of_cross_register_changes_response

    def construct_cross_register_changes_success_response(self, cross_register_changes: List[CrossRegisterChangeRequestData], g2p_request: G2PRequest = None) -> CrossRegisterChangesDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: CrossRegisterChangesDataResponseBody = CrossRegisterChangesDataResponseBody(
            response_payload=CrossRegisterChangesData(cross_register_changes=cross_register_changes)
        )

        cross_register_changes_response: CrossRegisterChangesDataResponse = CrossRegisterChangesDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return cross_register_changes_response

    def construct_change_requests_success_response(self, change_requests_list: list = None, change_requests_data: ChangeRequestsData = None, g2p_request: G2PRequest = None, number_of_items: int = None, number_of_pages: int = None) -> ChangeRequestFlattenedDataResponse:
        """Construct success response for change requests with flattened payload data."""
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        # Return flattened change requests (list of dicts with change_payload fields at root level)
        if change_requests_list is not None:
            payload = change_requests_list
        elif change_requests_data is not None:
            payload = change_requests_data.change_requests
        else:
            payload = []

        pagination_response = None
        if number_of_items is not None and number_of_pages is not None:
            pagination_response = G2PPaginationResponse(
                number_of_items=number_of_items,
                number_of_pages=number_of_pages
            )

        response_body: ChangeRequestFlattenedDataResponseBody = ChangeRequestFlattenedDataResponseBody(
            response_payload=payload,
            pagination_response=pagination_response
        )

        change_requests_response: ChangeRequestFlattenedDataResponse = ChangeRequestFlattenedDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return change_requests_response

    def construct_change_request_data_success_response(self, change_request_data: ChangeRequestData, g2p_request: G2PRequest = None) -> ChangeRequestDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: ChangeRequestDataResponseBody = ChangeRequestDataResponseBody(
            response_payload=change_request_data
        )

        change_request_response: ChangeRequestDataResponse = ChangeRequestDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return change_request_response

    def construct_record_success_response(self, record_data: RecordData, g2p_request: G2PRequest = None) -> RecordDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RecordDataResponseBody = RecordDataResponseBody(
            response_payload=record_data
        )

        record_response: RecordDataResponse = RecordDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return record_response

    def construct_verifications_success_response(self, verifications_list: List[VerificationData] = None, verifications_data: VerificationsData = None, g2p_request: G2PRequest = None, number_of_items: int = None, number_of_pages: int = None) -> VerificationsDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        # Support both old (verifications_data) and new (verifications_list) parameters
        if verifications_list is not None:
            payload = VerificationsData(verifications=verifications_list)
        else:
            payload = verifications_data

        pagination_response = None
        if number_of_items is not None and number_of_pages is not None:
            pagination_response = G2PPaginationResponse(
                number_of_items=number_of_items,
                number_of_pages=number_of_pages
            )

        response_body: VerificationsDataResponseBody = VerificationsDataResponseBody(
            response_payload=payload,
            pagination_response=pagination_response
        )

        verifications_response: VerificationsDataResponse = VerificationsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return verifications_response

    def construct_verification_success_response(self, verification_data: VerificationData, g2p_request: G2PRequest = None) -> VerificationDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: VerificationDataResponseBody = VerificationDataResponseBody(
            response_payload=verification_data
        )

        verification_response: VerificationDataResponse = VerificationDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return verification_response

    def construct_ingestion_config_success_response(self, payload_data, response_class, g2p_request=None):
        """Generic method to construct success response for ingestion configuration endpoints"""
        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        # Determine the response body class based on response_class
        response_class_name = response_class.__name__
        if response_class_name == 'IncomingPartnerResponse':
            response_body = IncomingPartnerResponseBody(response_payload=payload_data)
        elif response_class_name == 'IncomingPartnersResponse':
            response_body = IncomingPartnersResponseBody(response_payload=payload_data)
        elif response_class_name == 'IncomingModelKeyPathResponse':
            response_body = IncomingModelKeyPathResponseBody(response_payload=payload_data)
        elif response_class_name == 'IncomingModelKeyPathListResponse':
            response_body = IncomingModelKeyPathListResponseBody(response_payload=payload_data)
        elif response_class_name == 'IncomingModelSemanticPatternResponse':
            response_body = IncomingModelSemanticPatternResponseBody(response_payload=payload_data)
        elif response_class_name == 'IncomingTemplateResponse':
            response_body = IncomingTemplateResponseBody(response_payload=payload_data)
        elif response_class_name == 'DataModelResponse':
            response_body = DataModelResponseBody(response_payload=payload_data)
        elif response_class_name == 'DataModelsResponse':
            response_body = DataModelsResponseBody(response_payload=payload_data)
        elif response_class_name == 'SubscriptionActivityLogsResponse':
            response_body = SubscriptionActivityLogsResponseBody(response_payload=payload_data)
        else:
            # Fallback for other response types
            response_body = G2PResponseBody(response_payload=payload_data)

        response = response_class(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return response

    def construct_deduplication_register_results_success_response(self, dedup_results_list: List = None, dedup_results_data: DeduplicationRegisterResultsData = None, g2p_request: G2PRequest = None, number_of_items: int = None, number_of_pages: int = None) -> DeduplicationRegisterResultsDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        # Support both old (dedup_results_data) and new (dedup_results_list) parameters
        if dedup_results_list is not None:
            payload = DeduplicationRegisterResultsData(results=dedup_results_list)
        else:
            payload = dedup_results_data

        pagination_response = None
        if number_of_items is not None and number_of_pages is not None:
            pagination_response = G2PPaginationResponse(
                number_of_items=number_of_items,
                number_of_pages=number_of_pages
            )

        response_body: DeduplicationRegisterResultsDataResponseBody = DeduplicationRegisterResultsDataResponseBody(
            response_payload=payload,
            pagination_response=pagination_response
        )

        dedup_results_response: DeduplicationRegisterResultsDataResponse = DeduplicationRegisterResultsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return dedup_results_response

    def construct_deduplication_changerequest_results_success_response(self, dedup_results_list: List = None, dedup_results_data: DeduplicationChangerequestResultsData = None, g2p_request: G2PRequest = None, number_of_items: int = None, number_of_pages: int = None) -> DeduplicationChangerequestResultsDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        # Support both old (dedup_results_data) and new (dedup_results_list) parameters
        if dedup_results_list is not None:
            payload = DeduplicationChangerequestResultsData(results=dedup_results_list)
        else:
            payload = dedup_results_data

        pagination_response = None
        if number_of_items is not None and number_of_pages is not None:
            pagination_response = G2PPaginationResponse(
                number_of_items=number_of_items,
                number_of_pages=number_of_pages
            )

        response_body: DeduplicationChangerequestResultsDataResponseBody = DeduplicationChangerequestResultsDataResponseBody(
            response_payload=payload,
            pagination_response=pagination_response
        )

        dedup_results_response: DeduplicationChangerequestResultsDataResponse = DeduplicationChangerequestResultsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return dedup_results_response

    def construct_outgestion_config_success_response(self, payload_data, response_class, g2p_request=None):
        """Generic method to construct success response for ingestion configuration endpoints"""
        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        # Determine the response body class based on response_class
        response_class_name = response_class.__name__
        if response_class_name == 'OutgoingTopicResponse':
            response_body = OutgoingTopicResponseBody(response_payload=payload_data)
        elif response_class_name == 'OutgoingTemplateResponse':
            response_body = OutgoingTemplateResponseBody(response_payload=payload_data)
        else:
            # Fallback for other response types
            response_body = G2PResponseBody(response_payload=payload_data)

        response = response_class(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return response

    def construct_register_schema_success_response(self, register_schema_data: RegisterSchemaData, g2p_request: G2PRequest = None) -> RegisterSchemaDataResponse:
        """Construct success response for get_register_schema endpoint."""
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RegisterSchemaDataResponseBody = RegisterSchemaDataResponseBody(
            response_payload=register_schema_data
        )

        register_schema_response: RegisterSchemaDataResponse = RegisterSchemaDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return register_schema_response

    def construct_register_data_success_response(self, register_data: RegisterData, g2p_request: G2PRequest = None) -> RegisterDataResponse:
        """Construct success response for create_register endpoint."""
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RegisterDataResponseBody = RegisterDataResponseBody(
            response_payload=register_data
        )

        register_data_response: RegisterDataResponse = RegisterDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return register_data_response

    def construct_register_sections_success_response(self, register_sections_list: List[RegisterSectionData], g2p_request: G2PRequest = None) -> RegisterSectionsDataResponse:
        """Construct success response for get_register_sections endpoint."""
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RegisterSectionsDataResponseBody = RegisterSectionsDataResponseBody(
            response_payload=register_sections_list
        )

        register_sections_response: RegisterSectionsDataResponse = RegisterSectionsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return register_sections_response

    def construct_register_section_success_response(self, register_section_data: RegisterSectionData, g2p_request: G2PRequest = None) -> RegisterSectionDataResponse:
        """Construct success response for get_schema_definition_for_register_section endpoint."""
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RegisterSectionDataResponseBody = RegisterSectionDataResponseBody(
            response_payload=register_section_data
        )

        register_section_response: RegisterSectionDataResponse = RegisterSectionDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return register_section_response

    def construct_register_tabs_success_response(self, register_tabs_list: List[RegisterUITabData], g2p_request: G2PRequest = None) -> RegisterTabsDataResponse:
        """Construct success response for get_register_tabs endpoint."""
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RegisterTabsDataResponseBody = RegisterTabsDataResponseBody(
            response_payload=register_tabs_list
        )

        register_tabs_response: RegisterTabsDataResponse = RegisterTabsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return register_tabs_response

    def construct_register_tab_success_response(self, register_tab_data: RegisterUITabData, g2p_request: G2PRequest = None) -> RegisterTabDataResponse:
        """Construct success response for add_register_tab endpoint."""
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RegisterTabDataResponseBody = RegisterTabDataResponseBody(
            response_payload=register_tab_data
        )

        register_tab_response: RegisterTabDataResponse = RegisterTabDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return register_tab_response

    def construct_section_records_success_response(
        self,
        section_records: List[RecordData],
        g2p_request: G2PRequest = None
    ) -> SectionRecordsDataResponse:
        """Construct success response for get_section_records endpoint."""
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: SectionRecordsDataResponseBody = SectionRecordsDataResponseBody(
            response_payload=section_records
        )

        section_records_response: SectionRecordsDataResponse = SectionRecordsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return section_records_response

    def construct_register_tab_records_success_response(
        self,
        tab_records: List[RegisterTabRecordData],
        g2p_request: G2PRequest = None
    ) -> RegisterTabRecordsDataResponse:
        """Construct success response for get_register_tab_records endpoint."""
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id if g2p_request else "",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RegisterTabRecordsDataResponseBody = RegisterTabRecordsDataResponseBody(
            response_payload=tab_records
        )

        tab_records_response: RegisterTabRecordsDataResponse = RegisterTabRecordsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return tab_records_response

    def construct_upload_documents_success_response(
        self,
        upload_response_data: UploadDocumentsResponseData
    ) -> UploadDocumentsResponse:
        """Construct success response for upload_change_request_documents endpoint."""
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: UploadDocumentsResponseBody = UploadDocumentsResponseBody(
            response_payload=upload_response_data
        )

        upload_response: UploadDocumentsResponse = UploadDocumentsResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return upload_response

    def construct_upload_documents_error_response(
        self,
        error_exception: Exception
    ) -> UploadDocumentsResponse:
        """Construct error response for upload_change_request_documents endpoint."""
        error_code = ""
        error_message = str(error_exception)

        if isinstance(error_exception, G2PRegistryException):
            error_code = error_exception.code
            error_message = error_exception.message

        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.ERROR,
            response_error_code=error_code,
            response_error_message=error_message,
            response_timestamp=datetime.now()
        )

        upload_response: UploadDocumentsResponse = UploadDocumentsResponse(
            response_header=g2p_response_header,
            response_body=None
        )
        return upload_response

    def construct_registry_configuration_data_success_response(
        self,
        registry_configuration_data: RegistryConfigurationData,
        g2p_request: G2PRequest = None
    ) -> RegistryConfigurationDataResponse:
        """Construct success response for registry configuration endpoints."""
        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: RegistryConfigurationDataResponseBody = RegistryConfigurationDataResponseBody(
            response_payload=registry_configuration_data
        )

        response: RegistryConfigurationDataResponse = RegistryConfigurationDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return response

    def construct_number_of_requests_pending_success_response(
        self,
        number_of_requests_pending_data: NumberOfRequestsPendingData,
        g2p_request: G2PRequest = None
    ) -> NumberOfRequestsPendingResponse:
        """Construct success response for get_number_of_requests_pending endpoint."""
        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: NumberOfRequestsPendingResponseBody = NumberOfRequestsPendingResponseBody(
            response_payload=number_of_requests_pending_data
        )

        response: NumberOfRequestsPendingResponse = NumberOfRequestsPendingResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return response

    def construct_earliest_pending_change_request_success_response(
        self,
        earliest_pending_change_request_data: EarliestPendingChangeRequestData,
        g2p_request: G2PRequest = None
    ) -> EarliestPendingChangeRequestResponse:
        """Construct success response for get_earliest_pending_change_request endpoint."""
        request_id = g2p_request.request_header.request_id if g2p_request else ""

        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id=request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: EarliestPendingChangeRequestResponseBody = EarliestPendingChangeRequestResponseBody(
            response_payload=earliest_pending_change_request_data
        )

        response: EarliestPendingChangeRequestResponse = EarliestPendingChangeRequestResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return response
