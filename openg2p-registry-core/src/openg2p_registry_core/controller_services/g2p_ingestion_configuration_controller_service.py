import logging
from openg2p_fastapi_common.service import BaseService

from ..services import G2PIngestionConfigurationService
from ..schemas import (
    IncomingPartnerPayload,
    IncomingPartnerUpdatePayload,
    IncomingPartnerData,
    IncomingModelSignaturePatternPayload,
    IncomingModelSignaturePatternUpdatePayload,
    IncomingModelSignaturePatternData,
)

_logger = logging.getLogger("g2p-ingestion-configuration-controller-service")


class G2PIngestionConfigurationControllerService(BaseService):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.g2p_ingestion_configuration_service = G2PIngestionConfigurationService.get_component()

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

