from datetime import datetime
from typing import List
from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.schemas import G2PRequest, G2PResponse, G2PResponseHeader, G2PResponseStatus, G2PResponseBody
from openg2p_registry_core.schemas import (
    ChangeLogPayload, ChangeLogResponse, ChangeLogResponseBody,
    RegisterSummaryData, RegisterSummaryDataResponse, RegisterSummaryDataResponseBody,
    RegisterData, AllRegistersResponse, AllRegistersResponseBody,
    ChildRegisterData, ChildRegistersResponse, ChildRegistersResponseBody,
    SearchResultData, SearchResultsResponse, SearchResultsResponseBody,
    ChangeLogSearchResultData, ChangeLogSearchResultsResponse, ChangeLogSearchResultsResponseBody,
    NumberOfVersionsData, NumberOfVersionsResponse, NumberOfVersionsResponseBody,
    NumberOfPendingChangeLogsData, NumberOfPendingChangeLogsResponse, NumberOfPendingChangeLogsResponseBody,
    ChangeLogData, ChangeLogDataResponse, ChangeLogDataResponseBody,
    ChangeLogsData, ChangeLogsDataResponse, ChangeLogsDataResponseBody,
    RecordData, RecordDataResponse, RecordDataResponseBody,
    VerificationsData, VerificationsDataResponse, VerificationsDataResponseBody,
    VerificationData, VerificationDataResponse, VerificationDataResponseBody,
    DeduplicationRegisterResultsData, DeduplicationRegisterResultsDataResponse, DeduplicationRegisterResultsDataResponseBody,
    DeduplicationChangelogResultsData, DeduplicationChangelogResultsDataResponse, DeduplicationChangelogResultsDataResponseBody,
    IncomingPartnerData, IncomingPartnerResponseBody,
    IncomingModelSignaturePatternData, IncomingModelSignaturePatternResponseBody,
    IncomingModelSemanticPatternResponseBody, IncomingTemplateResponseBody,
    IncomingPayloadEnricherResponseBody, DataModelResponseBody,
)
from openg2p_registry_core.errors import G2PRegistryException


class RequestResponseHelper(BaseService):
    def construct_change_log_success_response(self, change_log_payload: ChangeLogPayload, g2p_request: G2PRequest) -> ChangeLogResponse:

        g2p_response_header = G2PResponseHeader(
            request_id=g2p_request.request_header.request_id,
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )
        
        response_body: ChangeLogResponseBody = ChangeLogResponseBody(
            response_payload=change_log_payload
        )

        change_log_response: ChangeLogResponse = ChangeLogResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return change_log_response
    
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

    def construct_register_summary_data_success_response(self, register_summary_data_list: List[RegisterSummaryData]) -> RegisterSummaryDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
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

    def construct_all_registers_success_response(self, all_registers_list: List[RegisterData]) -> AllRegistersResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
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

    def construct_child_registers_success_response(self, child_registers_list: List[ChildRegisterData]) -> ChildRegistersResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
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

    def construct_search_results_success_response(self, search_results_list: List[SearchResultData]) -> SearchResultsResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: SearchResultsResponseBody = SearchResultsResponseBody(
            response_payload=search_results_list
        )

        search_results_response: SearchResultsResponse = SearchResultsResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return search_results_response

    def construct_change_log_search_results_success_response(self, search_results_list: List[ChangeLogSearchResultData]) -> ChangeLogSearchResultsResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: ChangeLogSearchResultsResponseBody = ChangeLogSearchResultsResponseBody(
            response_payload=search_results_list
        )

        change_log_search_results_response: ChangeLogSearchResultsResponse = ChangeLogSearchResultsResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return change_log_search_results_response

    def construct_number_of_versions_success_response(self, number_of_versions_data: NumberOfVersionsData) -> NumberOfVersionsResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
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

    def construct_number_of_pending_change_logs_success_response(self, number_of_pending_change_logs_data: NumberOfPendingChangeLogsData) -> NumberOfPendingChangeLogsResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: NumberOfPendingChangeLogsResponseBody = NumberOfPendingChangeLogsResponseBody(
            response_payload=number_of_pending_change_logs_data
        )

        number_of_pending_change_logs_response: NumberOfPendingChangeLogsResponse = NumberOfPendingChangeLogsResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return number_of_pending_change_logs_response

    def construct_change_logs_success_response(self, change_logs_data: ChangeLogsData) -> ChangeLogsDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: ChangeLogsDataResponseBody = ChangeLogsDataResponseBody(
            response_payload=change_logs_data
        )

        change_logs_response: ChangeLogsDataResponse = ChangeLogsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return change_logs_response

    def construct_record_success_response(self, record_data: RecordData) -> RecordDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
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

    def construct_verifications_success_response(self, verifications_data: VerificationsData) -> VerificationsDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: VerificationsDataResponseBody = VerificationsDataResponseBody(
            response_payload=verifications_data
        )

        verifications_response: VerificationsDataResponse = VerificationsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return verifications_response

    def construct_verification_success_response(self, verification_data: VerificationData) -> VerificationDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
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
        elif response_class_name == 'IncomingModelSignaturePatternResponse':
            response_body = IncomingModelSignaturePatternResponseBody(response_payload=payload_data)
        elif response_class_name == 'IncomingModelSemanticPatternResponse':
            response_body = IncomingModelSemanticPatternResponseBody(response_payload=payload_data)
        elif response_class_name == 'IncomingTemplateResponse':
            response_body = IncomingTemplateResponseBody(response_payload=payload_data)
        elif response_class_name == 'IncomingPayloadEnricherResponse':
            response_body = IncomingPayloadEnricherResponseBody(response_payload=payload_data)
        elif response_class_name == 'DataModelResponse':
            response_body = DataModelResponseBody(response_payload=payload_data)
        else:
            # Fallback for other response types
            response_body = G2PResponseBody(response_payload=payload_data)

        response = response_class(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return response

    def construct_deduplication_register_results_success_response(self, dedup_results_data: DeduplicationRegisterResultsData) -> DeduplicationRegisterResultsDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: DeduplicationRegisterResultsDataResponseBody = DeduplicationRegisterResultsDataResponseBody(
            response_payload=dedup_results_data
        )

        dedup_results_response: DeduplicationRegisterResultsDataResponse = DeduplicationRegisterResultsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return dedup_results_response

    def construct_deduplication_changelog_results_success_response(self, dedup_results_data: DeduplicationChangelogResultsData) -> DeduplicationChangelogResultsDataResponse:
        g2p_response_header: G2PResponseHeader = G2PResponseHeader(
            request_id="",
            response_status=G2PResponseStatus.SUCCESS,
            response_error_code="",
            response_error_message="",
            response_timestamp=datetime.now()
        )

        response_body: DeduplicationChangelogResultsDataResponseBody = DeduplicationChangelogResultsDataResponseBody(
            response_payload=dedup_results_data
        )

        dedup_results_response: DeduplicationChangelogResultsDataResponse = DeduplicationChangelogResultsDataResponse(
            response_header=g2p_response_header,
            response_body=response_body
        )
        return dedup_results_response

