import logging
from fastapi import UploadFile
from openg2p_fastapi_common.controller import BaseController
from typing import Optional

from openg2p_registry_core.controller_services import G2POutgestionConfigurationControllerService
from openg2p_registry_core.schemas import (
    OutgoingTopicData,
    OutgoingTopicRequest,
    OutgoingTopicUpdateRequest,
    OutgoingTopicResponse,
    OutgoingTemplateData,
    OutgoingTemplateRequest,
    OutgoingTemplateUpdateRequest,
    OutgoingTemplateResponse,
)

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class OutgestionConfigurationController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["Outgestion Configuration"]
        self.outgestion_config_service = G2POutgestionConfigurationControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/outgestion-config"

        # Websub Topic endpoints
        self.router.add_api_route(
            "/create_topic",
            self.create_outgoing_topic,
            responses={200: {"model": OutgoingTopicResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_all_topics",
            self.get_all_outgoing_topics,
            responses={200: {"model": OutgoingTopicResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_topic",
            self.get_outgoing_topic,
            responses={200: {"model": OutgoingTopicResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/update_topic",
            self.update_outgoing_topic,
            responses={200: {"model": OutgoingTopicResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/toggle_topicstatus",
            self.toggle_outgoing_topic_status,
            responses={200: {"model": OutgoingTopicResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/re_register_topic",
            self.rereregister_outgoing_topic,
            responses={200: {"model": OutgoingTopicResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/delete_topic",
            self.delete_outgoing_topic,
            responses={200: {"model": OutgoingTopicResponse}},
            methods=["POST"],
        )

        # OutgoingTemplate endpoints
        self.router.add_api_route(
            "/create_template",
            self.create_template,
            responses={200: {"model": OutgoingTemplateResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_template",
            self.get_template,
            responses={200: {"model": OutgoingTemplateResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/update_template",
            self.update_template,
            responses={200: {"model": OutgoingTemplateResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/delete_template",
            self.delete_template,
            responses={200: {"model": OutgoingTemplateResponse}},
            methods=["POST"],
        )


    async def create_outgoing_topic(
        self, topic_request: OutgoingTopicRequest
    ) -> OutgoingTopicResponse:
        try:
            topic_data: list[OutgoingTopicData] = await self.outgestion_config_service.create_outgoing_topic(
                topic_request.request_body.request_payload
            )
            return self.helper.construct_outgestion_config_success_response(
                topic_data, topic_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, topic_request)

    async def get_outgoing_topic(self, topic_request: OutgoingTopicRequest) -> OutgoingTopicResponse:
        try:
            topic_data: list[OutgoingTopicData] = await self.outgestion_config_service.get_outgoing_topic(topic_request.request_body.request_payload.topic_id)
            return self.helper.construct_outgestion_config_success_response(
                topic_data, topic_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, None)

    async def get_all_outgoing_topics(self, topic_request: OutgoingTopicRequest) -> OutgoingTopicResponse:
        try:
            topics_data: list[OutgoingTopicData] = await self.outgestion_config_service.get_all_outgoing_topics()
            return self.helper.construct_outgestion_config_success_response(
                topics_data, topic_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, None)

    async def update_outgoing_topic(
        self, outgoing_topic_update_request: OutgoingTopicUpdateRequest
    ) -> OutgoingTopicResponse:
        try:
            topic_data: list[OutgoingTopicData] = await self.outgestion_config_service.update_outgoing_topic(
                outgoing_topic_update_request.request_body.request_payload
            )
            return self.helper.construct_outgestion_config_success_response(
                topic_data, outgoing_topic_update_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, outgoing_topic_update_request)
        
    async def toggle_outgoing_topic_status(
        self, outgoing_topic_update_request: OutgoingTopicUpdateRequest
    ) -> OutgoingTopicResponse:
        try:
            topic_data = await self.outgestion_config_service.toggle_outgoing_topic_status(
                outgoing_topic_update_request.request_body.request_payload
            )
            return self.helper.construct_outgestion_config_success_response(
                topic_data, outgoing_topic_update_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, outgoing_topic_update_request)

    async def re_register_outgoing_topic(
        self, outgoing_topic_update_request: OutgoingTopicUpdateRequest
    ) -> OutgoingTopicResponse:
        try:
            topic_data = await self.outgestion_config_service.re_register_outgoing_topic(
                outgoing_topic_update_request.request_body.request_payload
            )
            return self.helper.construct_outgestion_config_success_response(
                topic_data, outgoing_topic_update_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, outgoing_topic_update_request)

    async def delete_outgoing_topic(
        self, outgoing_topic_update_request: OutgoingTopicUpdateRequest
    ) -> OutgoingTopicResponse:
        try:
            topic_data = await self.outgestion_config_service.delete_outgoing_topic(
                outgoing_topic_update_request.request_body.request_payload
            )
            return self.helper.construct_outgestion_config_success_response(
                topic_data, outgoing_topic_update_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, outgoing_topic_update_request)
    

    async def create_template(
        self, template_request: OutgoingTemplateRequest, template_file: UploadFile

    ) -> OutgoingTemplateResponse:
        try:
            template_data: OutgoingTemplateData = await self.outgestion_config_service.create_template(
                template_request.request_body.request_payload, template_file
            )
            return self.helper.construct_outgestion_config_success_response(
                template_data, template_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, template_request)

    async def get_template(self, template_request: OutgoingTemplateRequest) -> OutgoingTemplateResponse:
        try:
            template_data: OutgoingTemplateData = await self.outgestion_config_service.get_template(
                template_request.request_body.request_payload
            )
            return self.helper.construct_outgestion_config_success_response(
                template_data, template_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, template_request)

    async def update_template(
        self, template_update_request: OutgoingTemplateUpdateRequest, template_file: Optional[UploadFile] = None 
    ) -> OutgoingTemplateResponse:
        try:
            template_data: OutgoingTemplateData = await self.outgestion_config_service.update_template(
                template_update_request.request_body.request_payload, template_file
            )
            return self.helper.construct_outgestion_config_success_response(
                template_data, template_update_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, template_update_request)

    async def delete_template(self, template_delete_request: OutgoingTemplateUpdateRequest) -> OutgoingTemplateResponse:
        try:
            template_data: OutgoingTemplateData = await self.outgestion_config_service.delete_template(
                template_delete_request.request_body.request_payload
            )
            return self.helper.construct_outgestion_config_success_response(
                template_data, template_delete_request
            )
        except Exception as error:
            return self.helper.construct_error_response(error, template_delete_request)
