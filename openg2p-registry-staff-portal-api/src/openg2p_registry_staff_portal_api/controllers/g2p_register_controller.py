import logging
from openg2p_fastapi_common.controller import BaseController
from typing import Annotated
from fastapi import Depends

from openg2p_fastapi_auth.auth.factory import AuthFactory
from openg2p_fastapi_auth_models.schemas import AuthCredentials

from openg2p_registry_core.controller_services import G2PRegisterControllerService
from openg2p_registry_core.schemas import ChangeLogRequest, ChangeLogResponse, ChangeLogPayload
from openg2p_registry_core.errors import G2PRegistryException
from openg2p_fastapi_common.schemas import G2PResponse


from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PRegisterController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["G2P Register"]
        self.g2p_register_controller_service = G2PRegisterControllerService.get_component()
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


    async def create_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:
        #TODO: Validate Staff Token here with auth: Annotated[AuthCredentials, Depends(AuthFactory())]

        try:
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.create_change_log(change_log_request)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_payload=change_log_payload, g2p_request=change_log_request
            )
            return change_log_response
        except G2PRegistryException as gre:
            _logger.error(f"G2PRegistryException in create_change_log: {str(gre)}")
            error_response: G2PResponse = self.helper.construct_registry_error_response(gre, change_log_request)
            return error_response
        except Exception as e:
            _logger.error(f"Error in create_change_log: {str(e)}")
            error_response: G2PResponse = self.helper.construct_error_response(e, change_log_request)
            return error_response

    async def approve_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:

        try:
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.approve_change_log(change_log_request.request_body.request_payload.change_log_id)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_payload=change_log_payload, g2p_request=change_log_request
            )
            return change_log_response
        except G2PRegistryException as gre:
            _logger.error(f"G2PRegistryException in approve_change_log: {str(gre)}")
            error_response: G2PResponse = self.helper.construct_registry_error_response(gre, change_log_request)
            return error_response
        except Exception as e:
            _logger.error(f"Error in approve_change_log: {str(e)}")
            error_response: G2PResponse = self.helper.construct_error_response(e, change_log_request)
            return error_response
    
    async def reject_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponse:
        try:
            change_log_payload: ChangeLogPayload = await self.g2p_register_controller_service.reject_change_log(change_log_request.request_body.request_payload.change_log_id)
            change_log_response: ChangeLogResponse = self.helper.construct_change_log_success_response(
                change_log_payload=change_log_payload, g2p_request=change_log_request
            )
            return change_log_response
        except G2PRegistryException as gre:
            _logger.error(f"G2PRegistryException in reject_change_log: {str(gre)}")
            error_response: G2PResponse = self.helper.construct_registry_error_response(gre, change_log_request)
            return error_response
        except Exception as e:
            _logger.error(f"Error in reject_change_log: {str(e)}")
            error_response: G2PResponse = self.helper.construct_error_response(e, change_log_request)
            return error_response