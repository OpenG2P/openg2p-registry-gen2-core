import logging
from typing import Optional
from fastapi import UploadFile
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
    IncomingModelSemanticPatternRequest,
    IncomingModelSemanticPatternUpdateRequest,
    IncomingModelSemanticPatternResponse,
    IncomingTemplateRequest,
    IncomingTemplateUpdateRequest,
    IncomingTemplateResponse,
    IncomingTemplateData,
    IncomingPayloadEnricherRequest,
    IncomingPayloadEnricherUpdateRequest,
    IncomingPayloadEnricherResponse,
    DataModelRequest,
    DataModelUpdateRequest,
    DataModelResponse,
    SubscriptionActivityLogRequest,
    SubscriptionActivityLogsResponse,
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
            "/create_partner",
            self.create_incoming_partner,
            responses={200: {"model": IncomingPartnerResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_all_partners",
            self.get_all_incoming_partners,
            responses={200: {"model": IncomingPartnersResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_partner",
            self.get_incoming_partner,
            responses={200: {"model": IncomingPartnerResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/update_partner",
            self.update_incoming_partner,
            responses={200: {"model": IncomingPartnerResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/delete_partner",
            self.delete_incoming_partner,
            responses={200: {"model": IncomingPartnerResponse}},
            methods=["POST"],
        )

        # IncomingModelSignaturePattern endpoints
        self.router.add_api_route(
            "/create_signature_pattern",
            self.create_signature_pattern,
            responses={200: {"model": IncomingModelSignaturePatternResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_signature_pattern",
            self.get_signature_pattern,
            responses={200: {"model": IncomingModelSignaturePatternResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/update_signature_pattern",
            self.update_signature_pattern,
            responses={200: {"model": IncomingModelSignaturePatternResponse}},
            methods=["POST"],
        )

        # IncomingModelSemanticPattern endpoints
        self.router.add_api_route(
            "/create_semantic_pattern",
            self.create_semantic_pattern,
            responses={200: {"model": IncomingModelSemanticPatternResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_semantic_pattern",
            self.get_semantic_pattern,
            responses={200: {"model": IncomingModelSemanticPatternResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/update_semantic_pattern",
            self.update_semantic_pattern,
            responses={200: {"model": IncomingModelSemanticPatternResponse}},
            methods=["POST"],
        )

        # IncomingTemplate endpoints
        self.router.add_api_route(
            "/create_template",
            self.create_template,
            responses={200: {"model": IncomingTemplateResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_template",
            self.get_template,
            responses={200: {"model": IncomingTemplateResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/update_template",
            self.update_template,
            responses={200: {"model": IncomingTemplateResponse}},
            methods=["POST"],
        )

        # IncomingPayloadEnricher endpoints
        self.router.add_api_route(
            "/create_payload_enricher",
            self.create_payload_enricher,
            responses={200: {"model": IncomingPayloadEnricherResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_payload_enricher",
            self.get_payload_enricher,
            responses={200: {"model": IncomingPayloadEnricherResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/update_payload_enricher",
            self.update_payload_enricher,
            responses={200: {"model": IncomingPayloadEnricherResponse}},
            methods=["POST"],
        )

        # DataModel endpoints
        self.router.add_api_route(
            "/create_data_model",
            self.create_data_model,
            responses={200: {"model": DataModelResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_data_model",
            self.get_data_model,
            responses={200: {"model": DataModelResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/update_data_model",
            self.update_data_model,
            responses={200: {"model": DataModelResponse}},
            methods=["POST"],
        )

        # SubscriptionActivityLog endpoints
        self.router.add_api_route(
            "/create_subscription_activity_log",
            self.create_subscription_activity_log,
            responses={200: {"model": SubscriptionActivityLogsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_subscription_activity_logs_by_partner",
            self.get_subscription_activity_logs_by_partner,
            responses={200: {"model": SubscriptionActivityLogsResponse}},
            methods=["POST"],
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

    async def get_incoming_partner(self, partner_request: IncomingPartnerRequest) -> IncomingPartnerResponse:
        try:
            partner_data = await self.ingestion_config_service.get_incoming_partner(
                partner_request.request_body.request_payload.partner_id
            )
            return self.helper.construct_ingestion_config_success_response(
                partner_data, IncomingPartnerResponse, partner_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, partner_request)

    async def get_all_incoming_partners(self, partner_request: IncomingPartnerRequest) -> IncomingPartnersResponse:
        try:
            partners_data = await self.ingestion_config_service.get_all_incoming_partners()
            return self.helper.construct_ingestion_config_success_response(
                partners_data, IncomingPartnersResponse, partner_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, partner_request)

    async def update_incoming_partner(
        self, incoming_partner_request: IncomingPartnerUpdateRequest
    ) -> IncomingPartnerResponse:
        try:
            partner_data = await self.ingestion_config_service.update_incoming_partner(
                incoming_partner_request.request_body.request_payload.partner_id,
                incoming_partner_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                partner_data, IncomingPartnerResponse, incoming_partner_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, incoming_partner_request)

    async def delete_incoming_partner(self, incoming_partner_request: IncomingPartnerUpdateRequest) -> IncomingPartnerResponse:
        try:
            await self.ingestion_config_service.delete_incoming_partner(
                incoming_partner_request.request_body.request_payload.partner_id
            )
            return self.helper.construct_ingestion_config_success_response(
                None, IncomingPartnerResponse, incoming_partner_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, incoming_partner_request)

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
        self, pattern_request: IncomingModelSignaturePatternRequest
    ) -> IncomingModelSignaturePatternResponse:
        try:
            pattern_data = await self.ingestion_config_service.get_signature_pattern(
                pattern_request.request_body.request_payload.signature_pattern_id
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelSignaturePatternResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def update_signature_pattern(
        self, pattern_request: IncomingModelSignaturePatternUpdateRequest
    ) -> IncomingModelSignaturePatternResponse:
        try:
            pattern_data = await self.ingestion_config_service.update_signature_pattern(
                pattern_request.request_body.request_payload.signature_pattern_id,
                pattern_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelSignaturePatternResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def create_semantic_pattern(
        self, pattern_request: IncomingModelSemanticPatternRequest
    ) -> IncomingModelSemanticPatternResponse:
        try:
            pattern_data = await self.ingestion_config_service.create_semantic_pattern(
                pattern_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelSemanticPatternResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def get_semantic_pattern(
        self, pattern_request: IncomingModelSemanticPatternRequest
    ) -> IncomingModelSemanticPatternResponse:
        try:
            pattern_data = await self.ingestion_config_service.get_semantic_pattern(
                pattern_request.request_body.request_payload.semantic_pattern_id
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelSemanticPatternResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def update_semantic_pattern(
        self, pattern_request: IncomingModelSemanticPatternUpdateRequest
    ) -> IncomingModelSemanticPatternResponse:
        try:
            pattern_data = await self.ingestion_config_service.update_semantic_pattern(
                pattern_request.request_body.request_payload.semantic_pattern_id,
                pattern_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelSemanticPatternResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def create_template(
        self, template_request: IncomingTemplateRequest, template_file: UploadFile
    ) -> IncomingTemplateResponse:
        try:
            template_data: IncomingTemplateData = await self.ingestion_config_service.create_template(
                template_request.request_body.request_payload, template_file
            )
            return self.helper.construct_ingestion_config_success_response(
                template_data, IncomingTemplateResponse, template_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, template_request)

    async def get_template(self, template_request: IncomingTemplateRequest) -> IncomingTemplateResponse:
        try:
            template_data: IncomingTemplateData = await self.ingestion_config_service.get_template(
                template_request.request_body.request_payload.template_id
            )
            return self.helper.construct_ingestion_config_success_response(
                template_data, IncomingTemplateResponse, template_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, template_request)

    async def update_template(
        self, template_update_request: IncomingTemplateUpdateRequest, template_file: Optional[UploadFile] = None
    ) -> IncomingTemplateResponse:
        try:
            template_data: IncomingTemplateData = await self.ingestion_config_service.update_template(
                template_update_request.request_body.request_payload, template_file
            )
            return self.helper.construct_ingestion_config_success_response(
                template_data, IncomingTemplateResponse, template_update_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, template_update_request)

    async def create_payload_enricher(
        self, enricher_request: IncomingPayloadEnricherRequest
    ) -> IncomingPayloadEnricherResponse:
        try:
            enricher_data = await self.ingestion_config_service.create_payload_enricher(
                enricher_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                enricher_data, IncomingPayloadEnricherResponse, enricher_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, enricher_request)

    async def get_payload_enricher(
        self, enricher_request: IncomingPayloadEnricherRequest
    ) -> IncomingPayloadEnricherResponse:
        try:
            enricher_data = await self.ingestion_config_service.get_payload_enricher(
                enricher_request.request_body.request_payload.incoming_factory_id
            )
            return self.helper.construct_ingestion_config_success_response(
                enricher_data, IncomingPayloadEnricherResponse, enricher_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, enricher_request)

    async def update_payload_enricher(
        self, enricher_request: IncomingPayloadEnricherUpdateRequest
    ) -> IncomingPayloadEnricherResponse:
        try:
            enricher_data = await self.ingestion_config_service.update_payload_enricher(
                enricher_request.request_body.request_payload.incoming_factory_id,
                enricher_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                enricher_data, IncomingPayloadEnricherResponse, enricher_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, enricher_request)

    async def create_data_model(
        self, data_model_request: DataModelRequest
    ) -> DataModelResponse:
        try:
            data_model_data = await self.ingestion_config_service.create_data_model(
                data_model_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                data_model_data, DataModelResponse, data_model_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, data_model_request)

    async def get_data_model(self, data_model_request: DataModelRequest) -> DataModelResponse:
        try:
            data_model_data = await self.ingestion_config_service.get_data_model(
                data_model_request.request_body.request_payload.data_model_id
            )
            return self.helper.construct_ingestion_config_success_response(
                data_model_data, DataModelResponse, data_model_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, data_model_request)

    async def update_data_model(
        self, data_model_request: DataModelUpdateRequest
    ) -> DataModelResponse:
        try:
            data_model_data = await self.ingestion_config_service.update_data_model(
                data_model_request.request_body.request_payload.data_model_id,
                data_model_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                data_model_data, DataModelResponse, data_model_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, data_model_request)

    async def create_subscription_activity_log(
        self, subscription_activity_log_request: SubscriptionActivityLogRequest
    ) -> SubscriptionActivityLogsResponse:
        try:
            activity_log_data = await self.ingestion_config_service.create_subscription_activity_log(
                subscription_activity_log_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                [activity_log_data], SubscriptionActivityLogsResponse, subscription_activity_log_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, subscription_activity_log_request)

    async def get_subscription_activity_logs_by_partner(
        self, activity_log_request: SubscriptionActivityLogRequest
    ) -> SubscriptionActivityLogsResponse:
        try:
            activity_logs_data = await self.ingestion_config_service.get_subscription_activity_logs_by_partner(
                activity_log_request.request_body.request_payload.partner_id
            )
            return self.helper.construct_ingestion_config_success_response(
                activity_logs_data, SubscriptionActivityLogsResponse, activity_log_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, activity_log_request)

