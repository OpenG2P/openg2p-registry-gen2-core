from openg2p_fastapi_common.service import BaseService
from typing import JSON


class IngestionEnricherInterface(BaseService):

    def EnrichPayload(self, payload: JSON) -> JSON:
        raise NotImplementedError("EnrichPayload method not implemented")