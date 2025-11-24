import logging

from openg2p_registry_core.services import G2PPayloadEnricherService

_logger = logging.getLogger('g2p-enricher-service')

class G2PDciEnricherService(G2PPayloadEnricherService):
    pass

class G2PSpdciEnricherService(G2PPayloadEnricherService):
    pass

class G2PUndpEnricherService(G2PPayloadEnricherService):
    pass
