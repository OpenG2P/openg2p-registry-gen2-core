import logging
from typing import Dict, Optional

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from ..models import IncomingRawData
from ..services import G2PPartnerService
from ..schemas import IngestDataPayload

_logger = logging.getLogger('g2p-partner-contoller-service')
_engine = dbengine.get()

class G2PPartnerControllerService(BaseService):

    async def ingest_data(self, data_model: Optional[str], ingest_data: Dict) -> IngestDataPayload:
        g2p_partner_service = G2PPartnerService.get_component()
        incoming_raw_data: IncomingRawData = await g2p_partner_service.ingest_data(data_model.upper() if data_model else None, ingest_data)

        ingest_data_payload: IngestDataPayload = await self._construct_ingest_data_payload(incoming_raw_data)
        return ingest_data_payload
    
    
    async def _construct_ingest_data_payload(self, incoming_raw_data: IncomingRawData) -> IngestDataPayload:
        ingest_data_payload = IngestDataPayload(
            ingest_id=incoming_raw_data.ingest_id
        )
        return ingest_data_payload
        
