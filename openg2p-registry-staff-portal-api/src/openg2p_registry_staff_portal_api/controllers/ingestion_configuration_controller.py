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
    IncomingModelSemanticPatternRequest,
    IncomingModelSemanticPatternUpdateRequest,
    IncomingModelSemanticPatternResponse,
    IncomingTemplateRequest,
    IncomingTemplateUpdateRequest,
    IncomingTemplateResponse,
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

        # IncomingModelSemanticPattern endpoints
        self.router.add_api_route(
            "/semantic-patterns",
            self.create_semantic_pattern,
            responses={200: {"model": IncomingModelSemanticPatternResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/semantic-patterns/{semantic_pattern_id}",
            self.get_semantic_pattern,
            responses={200: {"model": IncomingModelSemanticPatternResponse}},
            methods=["GET"],
        )

        self.router.add_api_route(
            "/semantic-patterns/{semantic_pattern_id}",
            self.update_semantic_pattern,
            responses={200: {"model": IncomingModelSemanticPatternResponse}},
            methods=["PATCH"],
        )

        # IncomingTemplate endpoints
        self.router.add_api_route(
            "/templates",
            self.create_template,
            responses={200: {"model": IncomingTemplateResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/templates/{template_id}",
            self.get_template,
            responses={200: {"model": IncomingTemplateResponse}},
            methods=["GET"],
        )

        self.router.add_api_route(
            "/templates/{template_id}",
            self.update_template,
            responses={200: {"model": IncomingTemplateResponse}},
            methods=["PATCH"],
        )

        # IncomingPayloadEnricher endpoints
        self.router.add_api_route(
            "/payload-enrichers",
            self.create_payload_enricher,
            responses={200: {"model": IncomingPayloadEnricherResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/payload-enrichers/{incoming_factory_id}",
            self.get_payload_enricher,
            responses={200: {"model": IncomingPayloadEnricherResponse}},
            methods=["GET"],
        )

        self.router.add_api_route(
            "/payload-enrichers/{incoming_factory_id}",
            self.update_payload_enricher,
            responses={200: {"model": IncomingPayloadEnricherResponse}},
            methods=["PATCH"],
        )

        # DataModel endpoints
        self.router.add_api_route(
            "/data-models",
            self.create_data_model,
            responses={200: {"model": DataModelResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/data-models/{data_model_id}",
            self.get_data_model,
            responses={200: {"model": DataModelResponse}},
            methods=["GET"],
        )

        self.router.add_api_route(
            "/data-models/{data_model_id}",
            self.update_data_model,
            responses={200: {"model": DataModelResponse}},
            methods=["PATCH"],
        )

        # SubscriptionActivityLog endpoints
        self.router.add_api_route(
            "/partners/{partner_id}/subscription_activity",
            self.create_subscription_activity_log,
            responses={200: {"model": SubscriptionActivityLogsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/partners/{partner_id}/subscription_activity",
            self.get_subscription_activity_logs_by_partner,
            responses={200: {"model": SubscriptionActivityLogsResponse}},
            methods=["GET"],
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
        self, semantic_pattern_id: str
    ) -> IncomingModelSemanticPatternResponse:
        try:
            pattern_data = await self.ingestion_config_service.get_semantic_pattern(
                semantic_pattern_id
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelSemanticPatternResponse, None
            )
        except Exception as error:
            return self.helper.construct_error_response(error, None)

    async def update_semantic_pattern(
        self, semantic_pattern_id: str, pattern_request: IncomingModelSemanticPatternUpdateRequest
    ) -> IncomingModelSemanticPatternResponse:
        try:
            pattern_data = await self.ingestion_config_service.update_semantic_pattern(
                semantic_pattern_id, pattern_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelSemanticPatternResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def create_template(
        self, template_request: IncomingTemplateRequest
    ) -> IncomingTemplateResponse:
        try:
            template_data = await self.ingestion_config_service.create_template(
                template_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                template_data, IncomingTemplateResponse, template_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, template_request)

    async def get_template(self, template_id: str) -> IncomingTemplateResponse:
        try:
            template_data = await self.ingestion_config_service.get_template(template_id)
            return self.helper.construct_ingestion_config_success_response(
                template_data, IncomingTemplateResponse, None
            )
        except Exception as error:
            return self.helper.construct_error_response(error, None)

    async def update_template(
        self, template_id: str, template_request: IncomingTemplateUpdateRequest
    ) -> IncomingTemplateResponse:
        try:
            template_data = await self.ingestion_config_service.update_template(
                template_id, template_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                template_data, IncomingTemplateResponse, template_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, template_request)

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
        self, incoming_factory_id: str
    ) -> IncomingPayloadEnricherResponse:
        try:
            enricher_data = await self.ingestion_config_service.get_payload_enricher(
                incoming_factory_id
            )
            return self.helper.construct_ingestion_config_success_response(
                enricher_data, IncomingPayloadEnricherResponse, None
            )
        except Exception as error:
            return self.helper.construct_error_response(error, None)

    async def update_payload_enricher(
        self, incoming_factory_id: str, enricher_request: IncomingPayloadEnricherUpdateRequest
    ) -> IncomingPayloadEnricherResponse:
        try:
            enricher_data = await self.ingestion_config_service.update_payload_enricher(
                incoming_factory_id, enricher_request.request_body.request_payload
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

    async def get_data_model(self, data_model_id: str) -> DataModelResponse:
        try:
            data_model_data = await self.ingestion_config_service.get_data_model(data_model_id)
            return self.helper.construct_ingestion_config_success_response(
                data_model_data, DataModelResponse, None
            )
        except Exception as error:
            return self.helper.construct_error_response(error, None)

    async def update_data_model(
        self, data_model_id: str, data_model_request: DataModelUpdateRequest
    ) -> DataModelResponse:
        try:
            data_model_data = await self.ingestion_config_service.update_data_model(
                data_model_id, data_model_request.request_body.request_payload
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
        self, partner_id: str
    ) -> SubscriptionActivityLogsResponse:
        try:
            activity_logs_data = await self.ingestion_config_service.get_subscription_activity_logs_by_partner(
                partner_id
            )
            return self.helper.construct_ingestion_config_success_response(
                activity_logs_data, SubscriptionActivityLogsResponse, None
            )
        except Exception as error:
            return self.helper.construct_error_response(error, None)

