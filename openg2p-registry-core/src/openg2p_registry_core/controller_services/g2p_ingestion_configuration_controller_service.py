import logging
from typing import Optional
from fastapi import UploadFile
from openg2p_fastapi_common.service import BaseService

from ..services import G2PIngestionConfigurationService, G2PTemplateService
from ..schemas import (
    IncomingPartnerPayload,
    IncomingPartnerUpdatePayload,
    IncomingPartnerData,
    IncomingModelSignaturePatternPayload,
    IncomingModelSignaturePatternUpdatePayload,
    IncomingModelSignaturePatternData,
    IncomingModelSemanticPatternPayload,
    IncomingModelSemanticPatternUpdatePayload,
    IncomingModelSemanticPatternData,
    IncomingTemplatePayload,
    IncomingTemplateUpdatePayload,
    IncomingTemplateData,
    IncomingPayloadEnricherPayload,
    IncomingPayloadEnricherUpdatePayload,
    IncomingPayloadEnricherData,
    DataModelPayload,
    DataModelUpdatePayload,
    DataModelData,
    SubscriptionActivityLogPayload,
    SubscriptionActivityLogData,
)

_logger = logging.getLogger("g2p-ingestion-configuration-controller-service")


class G2PIngestionConfigurationControllerService(BaseService):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.g2p_ingestion_configuration_service = G2PIngestionConfigurationService.get_component()
        self.g2p_template_service = G2PTemplateService.get_component()

    async def create_incoming_partner(
        self, incoming_partner_payload: IncomingPartnerPayload
    ) -> IncomingPartnerData:
        """Create a new incoming partner"""
        return await self.g2p_ingestion_configuration_service.create_incoming_partner(
            incoming_partner_payload
        )

    async def get_incoming_partner(self, partner_id: str) -> IncomingPartnerData:
        """Get incoming partner by ID"""
        return await self.g2p_ingestion_configuration_service.get_incoming_partner(partner_id)

    async def update_incoming_partner(
        self, partner_id: str, incoming_partner_payload: IncomingPartnerUpdatePayload
    ) -> IncomingPartnerData:
        """Update incoming partner"""
        return await self.g2p_ingestion_configuration_service.update_incoming_partner(
            partner_id, incoming_partner_payload
        )

    async def delete_incoming_partner(self, partner_id: str) -> None:
        """Soft delete incoming partner"""
        return await self.g2p_ingestion_configuration_service.delete_incoming_partner(partner_id)

    async def get_all_incoming_partners(self) -> list[IncomingPartnerData]:
        """Get all incoming partners"""
        return await self.g2p_ingestion_configuration_service.get_all_incoming_partners()

    async def create_signature_pattern(
        self, pattern_payload: IncomingModelSignaturePatternPayload
    ) -> IncomingModelSignaturePatternData:
        """Create a new signature pattern"""
        return await self.g2p_ingestion_configuration_service.create_signature_pattern(
            pattern_payload
        )

    async def get_signature_pattern(
        self, signature_pattern_id: str
    ) -> IncomingModelSignaturePatternData:
        """Get signature pattern by ID"""
        return await self.g2p_ingestion_configuration_service.get_signature_pattern(
            signature_pattern_id
        )

    async def update_signature_pattern(
        self, signature_pattern_id: str, pattern_payload: IncomingModelSignaturePatternUpdatePayload
    ) -> IncomingModelSignaturePatternData:
        """Update signature pattern"""
        return await self.g2p_ingestion_configuration_service.update_signature_pattern(
            signature_pattern_id, pattern_payload
        )

    async def create_semantic_pattern(
        self, pattern_payload: IncomingModelSemanticPatternPayload
    ) -> IncomingModelSemanticPatternData:
        """Create a new semantic pattern"""
        return await self.g2p_ingestion_configuration_service.create_semantic_pattern(
            pattern_payload
        )

    async def get_semantic_pattern(
        self, semantic_pattern_id: str
    ) -> IncomingModelSemanticPatternData:
        """Get semantic pattern by ID"""
        return await self.g2p_ingestion_configuration_service.get_semantic_pattern(
            semantic_pattern_id
        )

    async def update_semantic_pattern(
        self, semantic_pattern_id: str, pattern_payload: IncomingModelSemanticPatternUpdatePayload
    ) -> IncomingModelSemanticPatternData:
        """Update semantic pattern"""
        return await self.g2p_ingestion_configuration_service.update_semantic_pattern(
            semantic_pattern_id, pattern_payload
        )

    async def create_template(
        self, template_payload: IncomingTemplatePayload, template_file: UploadFile
    ) -> IncomingTemplateData:
        """Create a new template"""
        return await self.g2p_template_service.create_incoming_template(
            template_payload, template_file
        )

    async def get_template(self, template_id: str) -> IncomingTemplateData:
        """Get template by ID"""
        return await self.g2p_template_service.get_incoming_template(template_id)

    async def update_template(
        self, template_update_payload: IncomingTemplateUpdatePayload, template_file: Optional[UploadFile] = None
    ) -> IncomingTemplateData:
        """Update template"""
        return await self.g2p_template_service.update_incoming_template(
            template_update_payload, template_file
        )

    async def delete_template(self, template_delete_payload: IncomingTemplateUpdatePayload) -> IncomingTemplateData:
        """Delete template"""
        return await self.g2p_template_service.delete_incoming_template(template_delete_payload.template_id)

    async def create_payload_enricher(
        self, enricher_payload: IncomingPayloadEnricherPayload
    ) -> IncomingPayloadEnricherData:
        """Create a new payload enricher"""
        return await self.g2p_ingestion_configuration_service.create_payload_enricher(
            enricher_payload
        )

    async def get_payload_enricher(
        self, incoming_factory_id: str
    ) -> IncomingPayloadEnricherData:
        """Get payload enricher by ID"""
        return await self.g2p_ingestion_configuration_service.get_payload_enricher(
            incoming_factory_id
        )

    async def update_payload_enricher(
        self, incoming_factory_id: str, enricher_payload: IncomingPayloadEnricherUpdatePayload
    ) -> IncomingPayloadEnricherData:
        """Update payload enricher"""
        return await self.g2p_ingestion_configuration_service.update_payload_enricher(
            incoming_factory_id, enricher_payload
        )

    async def create_data_model(
        self, data_model_payload: DataModelPayload
    ) -> DataModelData:
        """Create a new data model"""
        return await self.g2p_ingestion_configuration_service.create_data_model(
            data_model_payload
        )

    async def get_data_model(self, data_model_id: str) -> DataModelData:
        """Get data model by ID"""
        return await self.g2p_ingestion_configuration_service.get_data_model(data_model_id)

    async def update_data_model(
        self, data_model_id: str, data_model_payload: DataModelUpdatePayload
    ) -> DataModelData:
        """Update data model"""
        return await self.g2p_ingestion_configuration_service.update_data_model(
            data_model_id, data_model_payload
        )

    async def create_subscription_activity_log(
        self, subscription_activity_log_payload: SubscriptionActivityLogPayload
    ) -> SubscriptionActivityLogData:
        """Create a new subscription activity log"""
        return await self.g2p_ingestion_configuration_service.create_subscription_activity_log(
            subscription_activity_log_payload
        )

    async def get_subscription_activity_logs_by_partner(
        self, partner_id: str
    ) -> list[SubscriptionActivityLogData]:
        """Get all subscription activity logs for a partner"""
        return await self.g2p_ingestion_configuration_service.get_subscription_activity_logs_by_partner(
            partner_id
        )

