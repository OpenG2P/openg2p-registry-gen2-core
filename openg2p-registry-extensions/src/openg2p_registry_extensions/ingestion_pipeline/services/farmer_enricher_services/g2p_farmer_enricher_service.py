import logging
from typing import Dict

from .. import (
    G2PDciEnricherService,
    G2PUndpEnricherService,
    G2PSpdciEnricherService,
)

_logger = logging.getLogger('g2p-payload-enricher-service')

# DCI Payload Enrichers
class G2PDciFarmerCreateEnricherService(G2PDciEnricherService):
    def enrich(self, data: Dict):
        _logger.info("Processing G2PDciFarmerCreateEnricherService")
        return data

class G2PDciFarmerUpdateEnricherService(G2PDciEnricherService):
    def enrich(self, data: Dict):
        _logger.info("Processing G2PDciFarmerUpdateEnricherService")
        return data

class G2PDciFarmerDeleteEnricherService(G2PDciEnricherService):
    def enrich(self, data: Dict):
        _logger.info("Processing G2PDciFarmerDeleteEnricherService")
        return data

# SPDCI Payload Enrichers
class G2PSpdciFarmerCreateEnricherService(G2PSpdciEnricherService):
    def enrich(self, data: Dict):
        _logger.info("Processing G2PSpdciFarmerCreateEnricherService")
        return data

class G2PSpdciFarmerUpdateEnricherService(G2PSpdciEnricherService):
    def enrich(self, data: Dict):
        _logger.info("Processing G2PSpdciFarmerUpdateEnricherService")
        return data

class G2PSpdciFarmerDeleteEnricherService(G2PSpdciEnricherService):
    def enrich(self, data: Dict):
        _logger.info("Processing G2PSpdciFarmerDeleteEnricherService")
        return data

# UNDP Payload Enrichers
class G2PUndpFarmerCreateEnricherService(G2PUndpEnricherService):
    def enrich(self, data: Dict):
        _logger.info("Processing G2PUndpFarmerCreateEnricherService")
        return data

class G2PUndpFarmerUpdateEnricherService(G2PUndpEnricherService):
    def enrich(self, data: Dict):
        _logger.info("Processing G2PUndpFarmerUpdateEnricherService")
        return data

class G2PUndpFarmerDeleteEnricherService(G2PUndpEnricherService):
    def enrich(self, data: Dict):
        _logger.info("Processing G2PUndpFarmerDeleteEnricherService")
        return data
