import logging
from typing import List
from openg2p_fastapi_common.service import BaseService

from ..services import G2PUIHelperService
from ..schemas import (
    G2PInputMechanismData,
)

_logger = logging.getLogger('g2p-ui-helper-controller-service')


class G2PUIHelperControllerService(BaseService):

    async def get_all_input_mechanisms(self) -> List[G2PInputMechanismData]:
        """Get all input mechanisms"""
        _logger.info("Fetching all input mechanisms through controller service")
        g2p_ui_helper_service = G2PUIHelperService.get_component()
        input_mechanism_data: List[G2PInputMechanismData] = await g2p_ui_helper_service.get_all_input_mechanisms()
        return input_mechanism_data
