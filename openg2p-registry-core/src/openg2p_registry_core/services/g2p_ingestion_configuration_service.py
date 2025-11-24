import logging
import uuid
from datetime import datetime

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select

from ..models import IncomingPartner, IncomingModelSignaturePattern
from ..schemas import (
    IncomingPartnerPayload,
    IncomingPartnerUpdatePayload,
    IncomingPartnerData,
    IncomingModelSignaturePatternPayload,
    IncomingModelSignaturePatternUpdatePayload,
    IncomingModelSignaturePatternData,
)
from ..errors import G2PRegistryErrorCodes, G2PRegistryException

_logger = logging.getLogger("g2p-ingestion-configuration-service")


class G2PIngestionConfigurationService(BaseService):

    async def create_incoming_partner(
        self, incoming_partner_payload: IncomingPartnerPayload
    ) -> IncomingPartnerData:
        """Create a new incoming partner"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Check if partner mnemonic already exists
            existing = await session.execute(
                select(IncomingPartner).where(
                    IncomingPartner.partner_mnemonic == incoming_partner_payload.partner_mnemonic
                )
            )
            if existing.scalar_one_or_none():
                raise G2PRegistryException(
                    code="PARTNER_ALREADY_EXISTS",
                    message=f"Partner with mnemonic {incoming_partner_payload.partner_mnemonic} already exists",
                )

            partner_id = incoming_partner_payload.partner_id or str(uuid.uuid4())
            partner = IncomingPartner(
                partner_id=partner_id,
                partner_mnemonic=incoming_partner_payload.partner_mnemonic,
                keymanager_reference_id=incoming_partner_payload.keymanager_reference_id,
                is_active=incoming_partner_payload.is_active,
            )
            session.add(partner)
            await session.commit()
            await session.refresh(partner)
            return IncomingPartnerData.from_orm(partner)

    async def get_incoming_partner(self, partner_id: str) -> IncomingPartnerData:
        """Get incoming partner by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            partner = await session.execute(
                select(IncomingPartner).where(IncomingPartner.partner_id == partner_id)
            )
            partner_obj = partner.scalar_one_or_none()
            if not partner_obj:
                raise G2PRegistryException(
                    code="PARTNER_NOT_FOUND",
                    message=f"Partner with ID {partner_id} not found",
                )
            return IncomingPartnerData.from_orm(partner_obj)

    async def update_incoming_partner(
        self, partner_id: str, incoming_partner_payload: IncomingPartnerUpdatePayload
    ) -> IncomingPartnerData:
        """Update incoming partner - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            partner = await session.execute(
                select(IncomingPartner).where(IncomingPartner.partner_id == partner_id)
            )
            partner_obj = partner.scalar_one_or_none()
            if not partner_obj:
                raise G2PRegistryException(
                    code="PARTNER_NOT_FOUND",
                    message=f"Partner with ID {partner_id} not found",
                )

            # Only update fields that are provided (not None)
            if incoming_partner_payload.partner_mnemonic is not None:
                partner_obj.partner_mnemonic = incoming_partner_payload.partner_mnemonic
            if incoming_partner_payload.keymanager_reference_id is not None:
                partner_obj.keymanager_reference_id = incoming_partner_payload.keymanager_reference_id
            if incoming_partner_payload.is_active is not None:
                partner_obj.is_active = incoming_partner_payload.is_active

            await session.commit()
            await session.refresh(partner_obj)
            return IncomingPartnerData.from_orm(partner_obj)

    async def delete_incoming_partner(self, partner_id: str) -> None:
        """Soft delete incoming partner"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            partner = await session.execute(
                select(IncomingPartner).where(IncomingPartner.partner_id == partner_id)
            )
            partner_obj = partner.scalar_one_or_none()
            if not partner_obj:
                raise G2PRegistryException(
                    code="PARTNER_NOT_FOUND",
                    message=f"Partner with ID {partner_id} not found",
                )

            partner_obj.is_active = False
            await session.commit()

    async def create_signature_pattern(
        self, pattern_payload: IncomingModelSignaturePatternPayload
    ) -> IncomingModelSignaturePatternData:
        """Create a new signature pattern"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern_id = pattern_payload.signature_pattern_id or str(uuid.uuid4())
            pattern = IncomingModelSignaturePattern(
                signature_pattern_id=pattern_id,
                data_model_id=pattern_payload.data_model_id,
                key_path_for_sender=pattern_payload.key_path_for_sender,
                key_path_for_signature=pattern_payload.key_path_for_signature,
            )
            session.add(pattern)
            await session.commit()
            await session.refresh(pattern)
            return IncomingModelSignaturePatternData.from_orm(pattern)

    async def get_signature_pattern(
        self, signature_pattern_id: str
    ) -> IncomingModelSignaturePatternData:
        """Get signature pattern by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern = await session.execute(
                select(IncomingModelSignaturePattern).where(
                    IncomingModelSignaturePattern.signature_pattern_id == signature_pattern_id
                )
            )
            pattern_obj = pattern.scalar_one_or_none()
            if not pattern_obj:
                raise G2PRegistryException(
                    code="PATTERN_NOT_FOUND",
                    message=f"Pattern with ID {signature_pattern_id} not found",
                )
            return IncomingModelSignaturePatternData.from_orm(pattern_obj)

    async def update_signature_pattern(
        self, signature_pattern_id: str, pattern_payload: IncomingModelSignaturePatternUpdatePayload
    ) -> IncomingModelSignaturePatternData:
        """Update signature pattern - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern = await session.execute(
                select(IncomingModelSignaturePattern).where(
                    IncomingModelSignaturePattern.signature_pattern_id == signature_pattern_id
                )
            )
            pattern_obj = pattern.scalar_one_or_none()
            if not pattern_obj:
                raise G2PRegistryException(
                    code="PATTERN_NOT_FOUND",
                    message=f"Pattern with ID {signature_pattern_id} not found",
                )

            # Only update fields that are provided (not None)
            if pattern_payload.key_path_for_sender is not None:
                pattern_obj.key_path_for_sender = pattern_payload.key_path_for_sender
            if pattern_payload.key_path_for_signature is not None:
                pattern_obj.key_path_for_signature = pattern_payload.key_path_for_signature

            await session.commit()
            await session.refresh(pattern_obj)
            return IncomingModelSignaturePatternData.from_orm(pattern_obj)

