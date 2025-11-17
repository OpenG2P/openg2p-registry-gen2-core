from openg2p_fastapi_common.service import BaseService
from openg2p_registry_core.services import G2PRegisterDomainService

from ..services import G2PRegisterFarmerDomainService

class G2PRegisterDomainFactory(BaseService):

    g2p_register_domain_service: G2PRegisterDomainService = None
    
    def get_domain_service(self, register_mnemonic: str) -> G2PRegisterDomainService:
        if register_mnemonic == "Farmer":
            g2p_register_domain_service = G2PRegisterFarmerDomainService.get_component()
            return g2p_register_domain_service