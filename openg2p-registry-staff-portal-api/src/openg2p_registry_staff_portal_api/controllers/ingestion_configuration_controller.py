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
    IncomingModelKeyPathRequest,
    IncomingModelKeyPathResponse,
    IncomingModelKeyPathListResponse,
    EditKeyPathForMessageIdRequest,
    EditKeyPathForSenderRequest,
    EditKeyPathForSignatureRequest,
    EditKeyPathForSignaturePayloadRequest,
    EditIsListRequest,
    EditKeyPathForListElementsRequest,
    DeleteIncomingKeyPathRequest,
    IncomingModelSemanticPatternRequest,
    IncomingModelSemanticPatternUpdateRequest,
    IncomingModelSemanticPatternResponse,
    IncomingTemplateRequest,
    IncomingTemplateUpdateRequest,
    IncomingTemplateResponse,
    IncomingTemplateData,
    DataModelRequest,
    DataModelUpdateRequest,
    DataModelResponse,
    DataModelsResponse,
    ChangeResponseTemplateFileRequest,
    ChangeActiveStatusRequest,
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

        # IncomingModelKeyPath endpoints
        self.router.add_api_route(
            "/create_new_incoming_key_path",
            self.create_new_incoming_key_path,
            responses={200: {"model": IncomingModelKeyPathResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_all_incoming_key_paths",
            self.get_all_incoming_key_paths,
            responses={200: {"model": IncomingModelKeyPathListResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/delete_incoming_key_path",
            self.delete_incoming_key_path,
            responses={200: {"model": IncomingModelKeyPathResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/edit_key_path_for_message_id",
            self.edit_key_path_for_message_id,
            responses={200: {"model": IncomingModelKeyPathResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/edit_key_path_for_sender",
            self.edit_key_path_for_sender,
            responses={200: {"model": IncomingModelKeyPathResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/edit_key_path_for_signature",
            self.edit_key_path_for_signature,
            responses={200: {"model": IncomingModelKeyPathResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/edit_key_path_for_signature_payload",
            self.edit_key_path_for_signature_payload,
            responses={200: {"model": IncomingModelKeyPathResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/edit_is_list",
            self.edit_is_list,
            responses={200: {"model": IncomingModelKeyPathResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/edit_key_path_for_list_elements",
            self.edit_key_path_for_list_elements,
            responses={200: {"model": IncomingModelKeyPathResponse}},
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

        self.router.add_api_route(
            "/delete_template",
            self.delete_template,
            responses={200: {"model": IncomingTemplateResponse}},
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
            "/get_all_data_models",
            self.get_all_data_models,
            responses={200: {"model": DataModelsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/update_data_model",
            self.update_data_model,
            responses={200: {"model": DataModelResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/delete_data_model",
            self.delete_data_model,
            responses={200: {"model": DataModelResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/change_response_template_file",
            self.change_response_template_file,
            responses={200: {"model": DataModelResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/change_active_status",
            self.change_active_status,
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

    # IncomingModelKeyPath Methods
    async def create_new_incoming_key_path(
        self, pattern_request: IncomingModelKeyPathRequest
    ) -> IncomingModelKeyPathResponse:
        try:
            pattern_data = await self.ingestion_config_service.create_new_incoming_key_path(
                pattern_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelKeyPathResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def get_all_incoming_key_paths(
        self, pattern_request: IncomingModelKeyPathRequest
    ) -> IncomingModelKeyPathListResponse:
        try:
            key_paths_data = await self.ingestion_config_service.get_all_incoming_key_paths()
            return self.helper.construct_ingestion_config_success_response(
                key_paths_data, IncomingModelKeyPathListResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def delete_incoming_key_path(
        self, pattern_request: DeleteIncomingKeyPathRequest
    ) -> IncomingModelKeyPathResponse:
        try:
            await self.ingestion_config_service.delete_incoming_key_path(
                pattern_request.request_body.request_payload.key_path_id
            )
            return self.helper.construct_ingestion_config_success_response(
                None, IncomingModelKeyPathResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def edit_key_path_for_message_id(
        self, pattern_request: EditKeyPathForMessageIdRequest
    ) -> IncomingModelKeyPathResponse:
        try:
            pattern_data = await self.ingestion_config_service.edit_key_path_for_message_id(
                pattern_request.request_body.request_payload.key_path_id,
                pattern_request.request_body.request_payload.keypath_for_message_id
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelKeyPathResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def edit_key_path_for_sender(
        self, pattern_request: EditKeyPathForSenderRequest
    ) -> IncomingModelKeyPathResponse:
        try:
            pattern_data = await self.ingestion_config_service.edit_key_path_for_sender(
                pattern_request.request_body.request_payload.key_path_id,
                pattern_request.request_body.request_payload.key_path_for_sender
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelKeyPathResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def edit_key_path_for_signature(
        self, pattern_request: EditKeyPathForSignatureRequest
    ) -> IncomingModelKeyPathResponse:
        try:
            pattern_data = await self.ingestion_config_service.edit_key_path_for_signature(
                pattern_request.request_body.request_payload.key_path_id,
                pattern_request.request_body.request_payload.key_path_for_signature
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelKeyPathResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def edit_key_path_for_signature_payload(
        self, pattern_request: EditKeyPathForSignaturePayloadRequest
    ) -> IncomingModelKeyPathResponse:
        try:
            pattern_data = await self.ingestion_config_service.edit_key_path_for_signature_payload(
                pattern_request.request_body.request_payload.key_path_id,
                pattern_request.request_body.request_payload.key_path_for_signature_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelKeyPathResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def edit_is_list(
        self, pattern_request: EditIsListRequest
    ) -> IncomingModelKeyPathResponse:
        try:
            pattern_data = await self.ingestion_config_service.edit_is_list(
                pattern_request.request_body.request_payload.key_path_id,
                pattern_request.request_body.request_payload.is_list
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelKeyPathResponse, pattern_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, pattern_request)

    async def edit_key_path_for_list_elements(
        self, pattern_request: EditKeyPathForListElementsRequest
    ) -> IncomingModelKeyPathResponse:
        try:
            pattern_data = await self.ingestion_config_service.edit_key_path_for_list_elements(
                pattern_request.request_body.request_payload.key_path_id,
                pattern_request.request_body.request_payload.keypath_for_list_elements
            )
            return self.helper.construct_ingestion_config_success_response(
                pattern_data, IncomingModelKeyPathResponse, pattern_request
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
    
    async def delete_template(self, template_delete_request: IncomingTemplateUpdateRequest) -> IncomingTemplateResponse:
        try:
            template_data: IncomingTemplateData = await self.ingestion_config_service.delete_template(
                template_delete_request.request_body.request_payload
            )
            return self.helper.construct_ingestion_config_success_response(
                template_data, IncomingTemplateResponse, template_delete_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, template_delete_request)

    async def create_data_model(
        self, data_model_request: DataModelRequest, response_template_file: Optional[UploadFile] = None
    ) -> DataModelResponse:
        try:
            data_model_data = await self.ingestion_config_service.create_data_model(
                data_model_request.request_body.request_payload, response_template_file
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

    async def get_all_data_models(self, data_model_request: DataModelRequest) -> DataModelsResponse:
        try:
            data_models_data = await self.ingestion_config_service.get_all_data_models()
            return self.helper.construct_ingestion_config_success_response(
                data_models_data, DataModelsResponse, data_model_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, data_model_request)

    async def update_data_model(
        self, data_model_request: DataModelUpdateRequest, response_template_file: Optional[UploadFile] = None
    ) -> DataModelResponse:
        try:
            data_model_data = await self.ingestion_config_service.update_data_model(
                data_model_request.request_body.request_payload.data_model_id,
                data_model_request.request_body.request_payload, response_template_file
            )
            return self.helper.construct_ingestion_config_success_response(
                data_model_data, DataModelResponse, data_model_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, data_model_request)

    async def delete_data_model(self, data_model_request: DataModelRequest) -> DataModelResponse:
        try:
            data_model_data = await self.ingestion_config_service.delete_data_model(
                data_model_request.request_body.request_payload.data_model_id
            )
            return self.helper.construct_ingestion_config_success_response(
                data_model_data, DataModelResponse, data_model_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, data_model_request)

    async def change_response_template_file(
        self, change_template_request: ChangeResponseTemplateFileRequest,
        response_template_file: Optional[UploadFile] = None
    ) -> DataModelResponse:
        try:
            data_model_data = await self.ingestion_config_service.change_response_template_file(
                change_template_request.request_body.request_payload.data_model_id,
                response_template_file
            )
            return self.helper.construct_ingestion_config_success_response(
                data_model_data, DataModelResponse, change_template_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, change_template_request)

    async def change_active_status(
        self, change_status_request: ChangeActiveStatusRequest
    ) -> DataModelResponse:
        try:
            data_model_data = await self.ingestion_config_service.change_active_status(
                change_status_request.request_body.request_payload.data_model_id,
                change_status_request.request_body.request_payload.is_active
            )
            return self.helper.construct_ingestion_config_success_response(
                data_model_data, DataModelResponse, change_status_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, change_status_request)

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

