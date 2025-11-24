import logging

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine


_logger = logging.getLogger('g2p-payload-enricher-service')
_engine = dbengine.get()

class G2PPayloadEnricherService(BaseService):
    async def process(self):
        _logger.info("Processing payload enricher")
        pass