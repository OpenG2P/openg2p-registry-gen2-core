import importlib
from openg2p_fastapi_common.service import BaseService
from openg2p_registry_core.services import G2PPayloadEnricherService

class G2PPayloadEnricherFactory(BaseService):
    
    def get_enricher_service(
        self,
        raw_payload_enricher_class: str,
    ) -> G2PPayloadEnricherService:

        module = importlib.import_module("..services", __package__)
        enricher_service = getattr(module, raw_payload_enricher_class)
        g2p_payload_enricher_service: G2PPayloadEnricherService = enricher_service()

        return g2p_payload_enricher_service
        