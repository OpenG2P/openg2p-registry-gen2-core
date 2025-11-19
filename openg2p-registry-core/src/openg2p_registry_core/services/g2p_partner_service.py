import logging
from typing import Dict, Tuple
import uuid

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.utils.crypto import KeymanagerCryptoHelper

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..errors import G2PRegistryErrorCodes, G2PRegistryException
from ..helpers import SignaturePatternMatcher
from ..models import (
    IncomingPartner,
    IncomingModelSignaturePattern,
    IncomingRawData,
    IncomingRawDataPayload,
    DataModel,
)

_logger = logging.getLogger("g2p-partner-service")
_engine = dbengine.get()


class G2PPartnerService(BaseService):
    async def ingest_data(self, data_model_mnemonic: str, ingest_data: Dict):
        _logger.info("Starting data ingestion with received request")
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)

        async with session_maker() as session:
            data_model: DataModel = await self._get_data_model_from_data_model_mnemonic(data_model_mnemonic, session)

            (incoming_partner, signature) = await self._match_model_signature_pattern(
                data_model.data_model_id, ingest_data, session
            )
            _logger.debug("Matched incoming model signature pattern")

            await self._validate_signature(incoming_partner.keymanager_reference_id, signature)
            _logger.debug("Verified request signature")

            ingest_id: str = str(uuid.uuid4())
            incoming_raw_data: IncomingRawData = self._construct_incoming_raw_data(
                ingest_id, incoming_partner.partner_id, data_model.data_model_id
            )
            incoming_raw_data_payload: IncomingRawDataPayload = (
                self._construct_incoming_raw_data_payload(ingest_id, ingest_data)
            )

            _logger.debug(f"Storing raw data and payload to db with ingest_id: {ingest_id}")
            session.add(incoming_raw_data)
            session.add(incoming_raw_data_payload)

            await session.commit()

            return incoming_raw_data

    async def _get_data_model_from_data_model_mnemonic(
        self, data_model_mnemonic: str, session: Session
    ) -> DataModel:
        data_model: DataModel = (
            await session.execute(
                select(DataModel).where(
                    DataModel.data_model_mnemonic == data_model_mnemonic
                )
            )
        ).scalar_one_or_none()

        if not data_model:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.DATA_MODEL_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.DATA_MODEL_NOT_FOUND.value[0],
            )
        return data_model

    async def _get_partner_from_partner_mnemonic(
        self, partner_mnemonic: str, session: Session
    ) -> IncomingPartner:
        partner: IncomingPartner = (
            await session.execute(
                select(IncomingPartner).where(
                    IncomingPartner.partner_mnemonic == partner_mnemonic
                )
            )
        ).scalar_one_or_none()

        if not partner:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.PARTNER_NOT_REGISTERED.value[1],
                message=G2PRegistryErrorCodes.PARTNER_NOT_REGISTERED.value[0],
            )
        return partner

    def _construct_incoming_raw_data(
        self, ingest_id: str, partner_id: str, data_model_id: int
    ) -> IncomingRawData:
        incoming_raw_data = IncomingRawData(
            ingest_id=ingest_id,
            partner_id=partner_id,
            data_model_id=data_model_id,
            receipt_date_time=func.now(),
        )
        return incoming_raw_data

    def _construct_incoming_raw_data_payload(
        self, ingest_id: str, ingest_data: Dict
    ) -> IncomingRawDataPayload:
        incoming_raw_data_payload = IncomingRawDataPayload(
            ingest_id=ingest_id,
            raw_data_json=ingest_data,
        )
        return incoming_raw_data_payload

    async def _match_model_signature_pattern(
        self, data_model_id: str, ingest_data: Dict, session: Session
    ) -> Tuple[IncomingPartner, str]:
        signature_pattern_matcher = SignaturePatternMatcher().get_component()
        
        incoming_model_signature_pattern = (
            await session.execute(
                select(IncomingModelSignaturePattern).where(
                    IncomingModelSignaturePattern.data_model_id == data_model_id
                )
            )
        ).scalar_one_or_none()
        partner_mnemonic, signature = signature_pattern_matcher.match(
            incoming_model_signature_pattern, ingest_data
        )
        # TODO: Create an error code for this case
        if not partner_mnemonic or not signature:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.PARTNER_NOT_REGISTERED.value[1],
                message=G2PRegistryErrorCodes.PARTNER_NOT_REGISTERED.value[0],
            )

        incoming_partner = await self._get_partner_from_partner_mnemonic(
            partner_mnemonic, session
        )

        return incoming_partner, signature

    async def _validate_signature(self, keymanager_reference_id: str, signature: str):
        keymanager_helper = KeymanagerCryptoHelper().get_component()
        signature_valid = await keymanager_helper.verify_jwt(
            self,
            orig_jwt=signature,
            payload=None,
            km_app_id=None,
            km_ref_id=keymanager_reference_id,
        )
        if not signature_valid:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1],
                message=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[0],
            )
