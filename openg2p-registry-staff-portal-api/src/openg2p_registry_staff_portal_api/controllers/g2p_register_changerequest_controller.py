import logging
from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PRegisterChangerequestControllerService
from openg2p_registry_core.schemas import (
    ChangeRequestRequest, ChangeRequestResponse, ChangeRequestResponsePayload,
    GetNumberOfPendingChangeRequestsRequest,
    GetNumberOfCrossRegisterChangesRequest,
    GetCrossRegisterChangesRequest,
    GetChangeRequestsRequest,
    GetChangeRequestRequest,
    GetVerificationsRequest,
    AddVerificationRequest,
    NumberOfPendingChangeRequestsResponse, NumberOfPendingChangeRequestsData,
    NumberOfCrossRegisterChangesResponse, NumberOfCrossRegisterChangesData,
    CrossRegisterChangeRequestData, CrossRegisterChangesDataResponse,
    ChangeRequestDataResponse, ChangeRequestData,
    ChangeRequestsDataResponse,
    VerificationsDataResponse,
    VerificationDataResponse, VerificationData,
)
from openg2p_fastapi_common.schemas import G2PResponse

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PRegisterChangerequestController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["G2P Register Changerequest"]
        self.g2p_register_changerequest_controller_service = G2PRegisterChangerequestControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/register"

        self.router.add_api_route(
            "/create_change_request",
            self.create_change_request,
            responses={200: {"model": ChangeRequestResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/approve_change_request",
            self.approve_change_request,
            responses={200: {"model": ChangeRequestResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/reject_change_request",
            self.reject_change_request,
            responses={200: {"model": ChangeRequestResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_number_of_pending_change_requests",
            self.get_number_of_pending_change_requests,
            responses={200: {"model": NumberOfPendingChangeRequestsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_number_of_cross_register_changes",
            self.get_number_of_cross_register_changes,
            responses={200: {"model": NumberOfCrossRegisterChangesResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_cross_register_changes",
            self.get_cross_register_changes,
            responses={200: {"model": CrossRegisterChangesDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_change_requests",
            self.get_change_requests,
            responses={200: {"model": ChangeRequestsDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_change_request",
            self.get_change_request,
            responses={200: {"model": ChangeRequestDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_verifications_for_change_request",
            self.get_verifications_for_change_request,
            responses={200: {"model": VerificationsDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/add_verification_for_change_request",
            self.add_verification_for_change_request,
            responses={200: {"model": VerificationDataResponse}},
            methods=["POST"],
        )

    async def create_change_request(self, change_request_request: ChangeRequestRequest) -> ChangeRequestResponse:
        try:
            change_request_response_payload: ChangeRequestResponsePayload = await self.g2p_register_changerequest_controller_service.create_change_request(change_request_request)
            change_request_response: ChangeRequestResponse = self.helper.construct_change_request_success_response(
                change_request_response_payload=change_request_response_payload, g2p_request=change_request_request
            )
            return change_request_response
        except Exception as error_exception:
            _logger.error(f"Error in create_change_request: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, change_request_request)
            return error_response

    async def approve_change_request(self, change_request_request: ChangeRequestRequest) -> ChangeRequestResponse:
        try:
            change_request_response_payload: ChangeRequestResponsePayload = await self.g2p_register_changerequest_controller_service.approve_change_request(change_request_request)
            change_request_response: ChangeRequestResponse = self.helper.construct_change_request_success_response(
                change_request_response_payload=change_request_response_payload, g2p_request=change_request_request
            )
            return change_request_response
        except Exception as error_exception:
            _logger.error(f"Error in approve_change_request: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, change_request_request)
            return error_response

    async def reject_change_request(self, change_request_request: ChangeRequestRequest) -> ChangeRequestResponse:
        try:
            change_request_response_payload: ChangeRequestResponsePayload = await self.g2p_register_changerequest_controller_service.reject_change_request(change_request_request)
            change_request_response: ChangeRequestResponse = self.helper.construct_change_request_success_response(
                change_request_response_payload=change_request_response_payload, g2p_request=change_request_request
            )
            return change_request_response
        except Exception as error_exception:
            _logger.error(f"Error in reject_change_request: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, change_request_request)
            return error_response

    async def get_number_of_pending_change_requests(self, get_number_of_pending_change_requests_request: GetNumberOfPendingChangeRequestsRequest) -> NumberOfPendingChangeRequestsResponse:
        try:
            number_of_pending_change_requests_data: NumberOfPendingChangeRequestsData = await self.g2p_register_changerequest_controller_service.get_number_of_pending_change_requests(get_number_of_pending_change_requests_request)
            number_of_pending_change_requests_response: NumberOfPendingChangeRequestsResponse = self.helper.construct_number_of_pending_change_requests_success_response(
                number_of_pending_change_requests_data=number_of_pending_change_requests_data, g2p_request=get_number_of_pending_change_requests_request
            )
            return number_of_pending_change_requests_response
        except Exception as error_exception:
            _logger.error(f"Error in get_number_of_pending_change_requests: {str(error_exception)}")
            error_response: NumberOfPendingChangeRequestsResponse = self.helper.construct_error_response(error_exception, get_number_of_pending_change_requests_request)
            return error_response

    async def get_number_of_cross_register_changes(self, get_number_of_cross_register_changes_request: GetNumberOfCrossRegisterChangesRequest) -> NumberOfCrossRegisterChangesResponse:
        try:
            number_of_cross_register_changes_data: NumberOfCrossRegisterChangesData = await self.g2p_register_changerequest_controller_service.get_number_of_cross_register_changes(get_number_of_cross_register_changes_request)
            number_of_cross_register_changes_response: NumberOfCrossRegisterChangesResponse = self.helper.construct_number_of_cross_register_changes_success_response(
                number_of_cross_register_changes_data=number_of_cross_register_changes_data, g2p_request=get_number_of_cross_register_changes_request
            )
            return number_of_cross_register_changes_response
        except Exception as error_exception:
            _logger.error(f"Error in get_number_of_cross_register_changes: {str(error_exception)}")
            error_response: NumberOfCrossRegisterChangesResponse = self.helper.construct_error_response(error_exception, get_number_of_cross_register_changes_request)
            return error_response

    async def get_cross_register_changes(self, get_cross_register_changes_request: GetCrossRegisterChangesRequest) -> CrossRegisterChangesDataResponse:
        try:
            cross_register_changes: list[CrossRegisterChangeRequestData] = await self.g2p_register_changerequest_controller_service.get_cross_register_changes(get_cross_register_changes_request)
            cross_register_changes_response: CrossRegisterChangesDataResponse = self.helper.construct_cross_register_changes_success_response(
                cross_register_changes=cross_register_changes, g2p_request=get_cross_register_changes_request
            )
            return cross_register_changes_response
        except Exception as error_exception:
            _logger.error(f"Error in get_cross_register_changes: {str(error_exception)}")
            error_response: CrossRegisterChangesDataResponse = self.helper.construct_error_response(error_exception, get_cross_register_changes_request)
            return error_response

    async def get_change_requests(self, get_change_requests_request: GetChangeRequestsRequest) -> ChangeRequestsDataResponse:
        try:
            change_requests_list, total_items, number_of_pages = await self.g2p_register_changerequest_controller_service.get_change_requests(get_change_requests_request)
            change_requests_response: ChangeRequestsDataResponse = self.helper.construct_change_requests_success_response(
                change_requests_list=change_requests_list, g2p_request=get_change_requests_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return change_requests_response
        except Exception as error_exception:
            _logger.error(f"Error in get_change_requests: {str(error_exception)}")
            error_response: ChangeRequestsDataResponse = self.helper.construct_error_response(error_exception, get_change_requests_request)
            return error_response

    async def get_change_request(self, get_change_request_request: GetChangeRequestRequest) -> ChangeRequestDataResponse:
        try:
            change_request_data: ChangeRequestData = await self.g2p_register_changerequest_controller_service.get_change_request(get_change_request_request)
            change_request_response: ChangeRequestDataResponse = self.helper.construct_change_request_data_success_response(
                change_request_data=change_request_data, g2p_request=get_change_request_request
            )
            return change_request_response
        except Exception as error_exception:
            _logger.error(f"Error in get_change_request: {str(error_exception)}")
            error_response: ChangeRequestDataResponse = self.helper.construct_error_response(error_exception, get_change_request_request)
            return error_response

    async def get_verifications_for_change_request(self, get_verifications_request: GetVerificationsRequest) -> VerificationsDataResponse:
        try:
            verifications_list, total_items, number_of_pages = await self.g2p_register_changerequest_controller_service.get_verifications_for_change_request(get_verifications_request)
            verifications_response: VerificationsDataResponse = self.helper.construct_verifications_success_response(
                verifications_list=verifications_list, g2p_request=get_verifications_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return verifications_response
        except Exception as error_exception:
            _logger.error(f"Error in get_verifications_for_change_request: {str(error_exception)}")
            error_response: VerificationsDataResponse = self.helper.construct_error_response(error_exception, get_verifications_request)
            return error_response

    async def add_verification_for_change_request(self, add_verification_request: AddVerificationRequest) -> VerificationDataResponse:
        try:
            verification_data: VerificationData = await self.g2p_register_changerequest_controller_service.add_verification_for_change_request(add_verification_request)
            verification_response: VerificationDataResponse = self.helper.construct_verification_success_response(
                verification_data=verification_data, g2p_request=add_verification_request
            )
            return verification_response
        except Exception as error_exception:
            _logger.error(f"Error in add_verification_for_change_request: {str(error_exception)}")
            error_response: VerificationDataResponse = self.helper.construct_error_response(error_exception, add_verification_request)
            return error_response

