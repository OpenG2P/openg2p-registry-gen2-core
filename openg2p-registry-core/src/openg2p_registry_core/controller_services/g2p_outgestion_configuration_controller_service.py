import logging
from fastapi import UploadFile
from typing import Optional
from openg2p_fastapi_common.service import BaseService

from ..services import G2POutgestionConfigurationService, G2PTemplateService
from ..schemas import (
    OutgoingTopicPayload,
    OutgoingTopicUpdatePayload,
    OutgoingTopicData,
    OutgoingTemplatePayload,
    OutgoingTemplateUpdatePayload,
    OutgoingTemplateData,
)

_logger = logging.getLogger("g2p-outgestion-configuration-controller-service")


class G2POutgestionConfigurationControllerService(BaseService):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.g2p_outgestion_configuration_service = G2POutgestionConfigurationService.get_component()
        self.g2p_template_service = G2PTemplateService.get_component()

    async def create_outgoing_topic(
        self, outgoing_topic_payload: OutgoingTopicPayload
    ) -> list[OutgoingTopicData]:
        """Create a new outgoing topic"""
        return await self.g2p_outgestion_configuration_service.create_outgoing_topic(
            outgoing_topic_payload
        )

    async def get_outgoing_topic(self, topic_id: str) -> list[OutgoingTopicData]:
        """Get outgoing topic by ID"""
        return await self.g2p_outgestion_configuration_service.get_outgoing_topic(topic_id)

    async def get_all_outgoing_topics(self) -> list[OutgoingTopicData]:
        """Get all outgoing topics"""
        return await self.g2p_outgestion_configuration_service.get_all_outgoing_topics()

    async def update_outgoing_topic(
        self, outgoing_topic_update_payload: OutgoingTopicUpdatePayload
    ) -> list[OutgoingTopicData]:
        """Update outgoing topic"""
        return await self.g2p_outgestion_configuration_service.update_outgoing_topic(
            outgoing_topic_update_payload
        )
    
    async def toggle_outgoing_topic_status(self, outgoing_topic_update_payload: OutgoingTopicUpdatePayload) -> list[OutgoingTopicData]:
        """Toggle outgoing topic status"""
        return await self.g2p_outgestion_configuration_service.toggle_outgoing_topic_status(outgoing_topic_update_payload.topic_id)
    
    async def re_register_outgoing_topic(self, outgoing_topic_update_payload: OutgoingTopicUpdatePayload) -> list[OutgoingTopicData]:
        """Re-register outgoing topic"""
        return await self.g2p_outgestion_configuration_service.re_register_outgoing_topic(outgoing_topic_update_payload.topic_id)

    async def delete_outgoing_topic(self, outgoing_topic_update_payload: OutgoingTopicUpdatePayload) -> list[OutgoingTopicData]:
        """Delete outgoing topic"""
        return await self.g2p_outgestion_configuration_service.delete_outgoing_topic(outgoing_topic_update_payload.topic_id)

    async def create_template(
        self, template_payload: OutgoingTemplatePayload, template_file: UploadFile
    ) -> OutgoingTemplateData:
        """Create a new template"""
        return await self.g2p_template_service.create_outgoing_template(
            template_payload, template_file
        )

    async def get_template(self, template_payload: OutgoingTemplatePayload) -> OutgoingTemplateData:
        """Get template by ID"""
        return await self.g2p_template_service.get_outgoing_template(template_payload.template_id)

    async def update_template(
        self, template_update_payload: OutgoingTemplateUpdatePayload, template_file: Optional[UploadFile] = None 
    ) -> OutgoingTemplateData:
        """Update template"""
        return await self.g2p_template_service.update_outgoing_template(
            template_update_payload, template_file
        )

    async def delete_template(self, template_delete_payload: OutgoingTemplateUpdatePayload) -> OutgoingTemplateData:
        """Delete template"""
        return await self.g2p_template_service.delete_outgoing_template(template_delete_payload.template_id)