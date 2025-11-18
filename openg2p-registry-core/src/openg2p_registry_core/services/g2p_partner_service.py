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
from ..models import IncomingModelSignaturePattern, IncomingRawData, IncomingRawDataPayload, DataModel, ProcessStatusEnum

_logger = logging.getLogger('g2p-partner-service')
_engine = dbengine.get()

class G2PPartnerService(BaseService):

    async def ingest_data(self, ingest_data: Dict):
        _logger.info("Starting data ingestion with received request")
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            (
                matched_model_signature_pattern,
                sender,
                signature,
                data_model
            ) = await self._match_signature_pattern(ingest_data, session)

            _logger.debug("Successfully matched ingest model signature pattern")

            await self._verify_signature(sender, signature)

            _logger.debug("Successfully verified signature")

            ingest_id: str = str(uuid.uuid4())
            data_model_id: int = await self._get_data_model_id(data_model, session)

            incoming_raw_data: IncomingRawData = self._construct_incoming_raw_data(ingest_id, matched_model_signature_pattern.partner_id, data_model_id)
            incoming_raw_data_payload: IncomingRawDataPayload = self._construct_incoming_raw_data_payload(ingest_id, ingest_data)

            _logger.debug(f"Storing raw data to db with ingest_id: {ingest_id}")
            session.add(incoming_raw_data)
            session.add(incoming_raw_data_payload)

            await session.commit()
            _logger.debug("Successfully stored raw data to db")

            return incoming_raw_data


    # Get data_model_id using data_model_mnemonic
    async def _get_data_model_id(self, data_model: str, session: Session) -> int:
        data_model_id = await session.execute(
            select(DataModel.data_model_id).where(DataModel.data_model_mnemonic == data_model)
        ).scalar_one_or_none()

        if not data_model_id:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.DATA_MODEL_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.DATA_MODEL_NOT_FOUND.value[0]
            )
        return data_model_id
    
    def _construct_incoming_raw_data(self, ingest_id: str, partner_id: str, data_model_id: int) -> IncomingRawData:
        incoming_raw_data = IncomingRawData(
            ingest_id=ingest_id,
            partner_id=partner_id,
            data_model_id=data_model_id,
            receipt_date_time=func.now(),
            process_status=ProcessStatusEnum.PENDING.value,
            process_date_time=None
        )
        return incoming_raw_data
    
    def _construct_incoming_raw_data_payload(self, ingest_id: str, ingest_data: Dict) -> IncomingRawDataPayload:
        incoming_raw_data_payload = IncomingRawDataPayload(
            ingest_id=ingest_id,
            raw_data_json=ingest_data,
        )
        return incoming_raw_data_payload
    
    async def _match_signature_pattern(self, ingest_data: Dict, session: Session) -> Tuple[IncomingModelSignaturePattern, str, str, str]:
        signature_pattern_matcher = SignaturePatternMatcher().get_component()
        (
            matched_model_signature_pattern,
            sender,
            signature,
            data_model
        ) = await signature_pattern_matcher.match(ingest_data, session)
        if not sender or not signature or not data_model:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.PARTNER_NOT_REGISTERED.value[1],
                message=G2PRegistryErrorCodes.PARTNER_NOT_REGISTERED.value[0]
            )
        return (matched_model_signature_pattern, sender, signature, data_model)
    
    async def _verify_signature(self, partner_mnemonic: str, signature: str):
        keymanager_helper = KeymanagerCryptoHelper().get_component()
        signature_valid = await keymanager_helper.verify_jwt(
            self,
            orig_jwt=signature,
            payload=None,
            km_app_id=None,
            km_ref_id=partner_mnemonic
        )
        if not signature_valid:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1],
                message=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[0]
            )
        
        