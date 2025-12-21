import logging
from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PRegisterChangelogControllerService
from openg2p_registry_core.schemas import (
    ChangeLogRequest, ChangeLogResponse, ChangeLogResponsePayload,
    GetNumberOfPendingChangeLogsRequest,
    GetNumberOfCrossRegisterChangesRequest,
    GetCrossRegisterChangesRequest,
    GetChangeLogsRequest,
    GetChangeLogRequest,
    GetVerificationsRequest,
    AddVerificationRequest,
    NumberOfPendingChangeLogsResponse, NumberOfPendingChangeLogsData,
    NumberOfCrossRegisterChangesResponse, NumberOfCrossRegisterChangesData,
    CrossRegisterChangeLogData, CrossRegisterChangesDataResponse,
    ChangeLogDataResponse, ChangeLogData,
    ChangeLogsDataResponse,
    VerificationsDataResponse,
    VerificationDataResponse, VerificationData,
)
from openg2p_fastapi_common.schemas import G2PResponse

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PRegisterChangelogController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["G2P Register Changelog"]
        self.g2p_register_changelog_controller_service = G2PRegisterChangelogControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/register"

        self.router.add_api_route(
            "/create_change_log",
            self.create_change_log,
            responses={200: {"model": ChangeLogResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/approve_change_log",
            self.approve_change_log,
            responses={200: {"model": ChangeLogResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/reject_change_log",
            self.reject_change_log,
            responses={200: {"model": ChangeLogResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_number_of_pending_change_logs",
            self.get_number_of_pending_change_logs,
            responses={200: {"model": NumberOfPendingChangeLogsResponse}},
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
            "/get_change_logs",
            self.get_change_logs,
            responses={200: {"model": ChangeLogsDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_change_log",
            self.get_change_log,
            responses={200: {"model": ChangeLogDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_verifications_for_change_log",
            self.get_verifications_for_change_log,
            responses={200: {"model": VerificationsDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/add_verification_for_change_log",
            self.add_verification_for_change_log,
            responses={200: {"model": VerificationDataResponse}},
            methods=["POST"],
        )

    async def create_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:
        try:
            change_log_response_payload: ChangeLogResponsePayload = await self.g2p_register_changelog_controller_service.create_change_log(change_log_request)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_response_payload=change_log_response_payload, g2p_request=change_log_request
            )
            return change_log_response
        except Exception as error_exception:
            _logger.error(f"Error in create_change_log: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, change_log_request)
            return error_response

    async def approve_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:
        try:
            change_log_response_payload: ChangeLogResponsePayload = await self.g2p_register_changelog_controller_service.approve_change_log(change_log_request)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_response_payload=change_log_response_payload, g2p_request=change_log_request
            )
            return change_log_response
        except Exception as error_exception:
            _logger.error(f"Error in approve_change_log: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, change_log_request)
            return error_response

    async def reject_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:
        try:
            change_log_response_payload: ChangeLogResponsePayload = await self.g2p_register_changelog_controller_service.reject_change_log(change_log_request)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_response_payload=change_log_response_payload, g2p_request=change_log_request
            )
            return change_log_response
        except Exception as error_exception:
            _logger.error(f"Error in reject_change_log: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, change_log_request)
            return error_response

    async def get_number_of_pending_change_logs(self, get_number_of_pending_change_logs_request: GetNumberOfPendingChangeLogsRequest) -> NumberOfPendingChangeLogsResponse:
        try:
            number_of_pending_change_logs_data: NumberOfPendingChangeLogsData = await self.g2p_register_changelog_controller_service.get_number_of_pending_change_logs(get_number_of_pending_change_logs_request)
            number_of_pending_change_logs_response: NumberOfPendingChangeLogsResponse = self.helper.construct_number_of_pending_change_logs_success_response(
                number_of_pending_change_logs_data=number_of_pending_change_logs_data, g2p_request=get_number_of_pending_change_logs_request
            )
            return number_of_pending_change_logs_response
        except Exception as error_exception:
            _logger.error(f"Error in get_number_of_pending_change_logs: {str(error_exception)}")
            error_response: NumberOfPendingChangeLogsResponse = self.helper.construct_error_response(error_exception, get_number_of_pending_change_logs_request)
            return error_response

    async def get_number_of_cross_register_changes(self, get_number_of_cross_register_changes_request: GetNumberOfCrossRegisterChangesRequest) -> NumberOfCrossRegisterChangesResponse:
        try:
            number_of_cross_register_changes_data: NumberOfCrossRegisterChangesData = await self.g2p_register_changelog_controller_service.get_number_of_cross_register_changes(get_number_of_cross_register_changes_request)
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
            cross_register_changes: list[CrossRegisterChangeLogData] = await self.g2p_register_changelog_controller_service.get_cross_register_changes(get_cross_register_changes_request)
            cross_register_changes_response: CrossRegisterChangesDataResponse = self.helper.construct_cross_register_changes_success_response(
                cross_register_changes=cross_register_changes, g2p_request=get_cross_register_changes_request
            )
            return cross_register_changes_response
        except Exception as error_exception:
            _logger.error(f"Error in get_cross_register_changes: {str(error_exception)}")
            error_response: CrossRegisterChangesDataResponse = self.helper.construct_error_response(error_exception, get_cross_register_changes_request)
            return error_response

    async def get_change_logs(self, get_change_logs_request: GetChangeLogsRequest) -> ChangeLogsDataResponse:
        try:
            change_logs_list, total_items, number_of_pages = await self.g2p_register_changelog_controller_service.get_change_logs(get_change_logs_request)
            change_logs_response: ChangeLogsDataResponse = self.helper.construct_change_logs_success_response(
                change_logs_list=change_logs_list, g2p_request=get_change_logs_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return change_logs_response
        except Exception as error_exception:
            _logger.error(f"Error in get_change_logs: {str(error_exception)}")
            error_response: ChangeLogsDataResponse = self.helper.construct_error_response(error_exception, get_change_logs_request)
            return error_response

    async def get_change_log(self, get_change_log_request: GetChangeLogRequest) -> ChangeLogDataResponse:
        try:
            change_log_data: ChangeLogData = await self.g2p_register_changelog_controller_service.get_change_log(get_change_log_request)
            change_log_response: ChangeLogDataResponse = self.helper.construct_change_log_data_success_response(
                change_log_data=change_log_data, g2p_request=get_change_log_request
            )
            return change_log_response
        except Exception as error_exception:
            _logger.error(f"Error in get_change_log: {str(error_exception)}")
            error_response: ChangeLogDataResponse = self.helper.construct_error_response(error_exception, get_change_log_request)
            return error_response

    async def get_verifications_for_change_log(self, get_verifications_request: GetVerificationsRequest) -> VerificationsDataResponse:
        try:
            verifications_list, total_items, number_of_pages = await self.g2p_register_changelog_controller_service.get_verifications_for_change_log(get_verifications_request)
            verifications_response: VerificationsDataResponse = self.helper.construct_verifications_success_response(
                verifications_list=verifications_list, g2p_request=get_verifications_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return verifications_response
        except Exception as error_exception:
            _logger.error(f"Error in get_verifications_for_change_log: {str(error_exception)}")
            error_response: VerificationsDataResponse = self.helper.construct_error_response(error_exception, get_verifications_request)
            return error_response

    async def add_verification_for_change_log(self, add_verification_request: AddVerificationRequest) -> VerificationDataResponse:
        try:
            verification_data: VerificationData = await self.g2p_register_changelog_controller_service.add_verification_for_change_log(add_verification_request)
            verification_response: VerificationDataResponse = self.helper.construct_verification_success_response(
                verification_data=verification_data, g2p_request=add_verification_request
            )
            return verification_response
        except Exception as error_exception:
            _logger.error(f"Error in add_verification_for_change_log: {str(error_exception)}")
            error_response: VerificationDataResponse = self.helper.construct_error_response(error_exception, add_verification_request)
            return error_response

