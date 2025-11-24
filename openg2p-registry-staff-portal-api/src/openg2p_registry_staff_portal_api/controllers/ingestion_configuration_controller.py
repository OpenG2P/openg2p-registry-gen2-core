import logging
from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PIngestionConfigurationControllerService
from openg2p_registry_core.schemas import (
    IncomingPartnerRequest,
    IncomingPartnerUpdateRequest,
    IncomingPartnerResponse,
    IncomingPartnersResponse,
    IncomingModelSignaturePatternRequest,
    IncomingModelSignaturePatternUpdateRequest,
    IncomingModelSignaturePatternResponse,
)

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class IngestionConfigurationController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["Ingestion Configuration"]
        self.ingestion_config_service = G2PIngestionConfigurationControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/ingestion-config"

        # IncomingPartner endpoints
        self.router.add_api_route(
            "/partners",
            self.create_incoming_partner,
            responses={200: {"model": IncomingPartnerResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/partners/{partner_id}",
            self.get_incoming_partner,
            responses={200: {"model": IncomingPartnerResponse}},
            methods=["GET"],
        )

        self.router.add_api_route(
            "/partners/{partner_id}",
            self.update_incoming_partner,
            responses={200: {"model": IncomingPartnerResponse}},
            methods=["PATCH"],
        )

        self.router.add_api_route(
            "/partners/{partner_id}",
            self.delete_incoming_partner,
            responses={200: {"model": IncomingPartnerResponse}},
            methods=["DELETE"],
        )

        # IncomingModelSignaturePattern endpoints
        self.router.add_api_route(
            "/signature-patterns",
            self.create_signature_pattern,
            responses={200: {"model": IncomingModelSignaturePatternResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/signature-patterns/{signature_pattern_id}",
            self.get_signature_pattern,
            responses={200: {"model": IncomingModelSignaturePatternResponse}},
            methods=["GET"],
        )

        self.router.add_api_route(
            "/signature-patterns/{signature_pattern_id}",
            self.update_signature_pattern,
            responses={200: {"model": IncomingModelSignaturePatternResponse}},
            methods=["PATCH"],
        )

    async def create_incoming_partner(
        self, incoming_partner_request: IncomingPartnerRequest
    ) -> IncomingPartnerResponse:
        try:
            partner_data = await self.ingestion_config_service.create_incoming_partner(
                incoming_partner_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                partner_data, IncomingPartnerResponse, incoming_partner_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, incoming_partner_request)

    async def get_incoming_partner(self, partner_id: str) -> IncomingPartnerResponse:
        try:
            partner_data = await self.ingestion_config_service.get_incoming_partner(partner_id)
            return self.helper.construct_ingestion_config_success_response(
                partner_data, IncomingPartnerResponse, None
            )
        except Exception as error:
            return self.helper.construct_error_response(error, None)

    async def update_incoming_partner(
        self, partner_id: str, incoming_partner_request: IncomingPartnerUpdateRequest
    ) -> IncomingPartnerResponse:
        try:
            partner_data = await self.ingestion_config_service.update_incoming_partner(
                partner_id, incoming_partner_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                partner_data, IncomingPartnerResponse, incoming_partner_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, incoming_partner_request)

    async def delete_incoming_partner(self, partner_id: str) -> IncomingPartnerResponse:
        try:
            await self.ingestion_config_service.delete_incoming_partner(partner_id)
            return self.helper.construct_ingestion_config_success_response(
                None, IncomingPartnerResponse, None
            )
        except Exception as error:
            return self.helper.construct_error_response(error, None)

    async def create_signature_pattern(
        self, pattern_request: IncomingModelSignaturePatternRequest
    ) -> IncomingModelSignaturePatternResponse:
        try:
            pattern_data = await self.ingestion_config_service.create_signature_pattern(
                pattern_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelSignaturePatternResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def get_signature_pattern(
        self, signature_pattern_id: str
    ) -> IncomingModelSignaturePatternResponse:
        try:
            pattern_data = await self.ingestion_config_service.get_signature_pattern(
                signature_pattern_id
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelSignaturePatternResponse, None
            )
        except Exception as error:
            return self.helper.construct_error_response(error, None)

    async def update_signature_pattern(
        self, signature_pattern_id: str, pattern_request: IncomingModelSignaturePatternUpdateRequest
    ) -> IncomingModelSignaturePatternResponse:
        try:
            pattern_data = await self.ingestion_config_service.update_signature_pattern(
                signature_pattern_id, pattern_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelSignaturePatternResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

