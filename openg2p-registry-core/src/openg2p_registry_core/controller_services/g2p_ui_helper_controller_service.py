import logging
from typing import List
from openg2p_fastapi_common.service import BaseService

from ..services import G2PUIHelperService
from ..schemas import (
    G2PInputMechanismData,
    G2PInputMechanismRequest
)

_logger = logging.getLogger('g2p-ui-helper-controller-service')


class G2PUIHelperControllerService(BaseService):

    async def get_all_input_mechanisms(self, request: G2PInputMechanismRequest) -> List[G2PInputMechanismData]:
        """Get all input mechanisms"""
        _logger.info("Fetching all input mechanisms through controller service")
        g2p_ui_helper_service = G2PUIHelperService.get_component()
        input_mechanism_data: List[G2PInputMechanismData] = await g2p_ui_helper_service.get_all_input_mechanisms(
            request.request_body.request_payload.register_id
        )
        return input_mechanism_data
