import logging
from typing import Dict
from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PPartnerControllerService
from openg2p_registry_core.schemas import IngestDataPayload, IngestDataRequest, IngestDataResponse
from openg2p_registry_core.errors import G2PRegistryException
from openg2p_fastapi_common.schemas import G2PResponse

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PPartnerController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["G2P Register Partner"]
        self.g2p_partner_controller_service = G2PPartnerControllerService.get_component()
        self.request_response_helper = RequestResponseHelper.get_component()
        self.router.prefix = "/partner"

        self.router.add_api_route(
            "/ingest_data",
            self.ingest_data,
            responses={200: {"model": IngestDataResponse}},
            methods=["POST"],
        )
    
    async def ingest_data(self, ingest_data_request: IngestDataRequest) -> IngestDataResponse:
        try:
            ingest_data: Dict = await ingest_data_request.json()
            ingest_data_payload: IngestDataPayload = await self.g2p_partner_controller_service.ingest_data(ingest_data)
            injest_data_response = self.request_response_helper.construct_ingest_data_success_response(ingest_data_payload, ingest_data_request)
            return injest_data_response
        
        except G2PRegistryException as gre:
            _logger.error(f"G2PRegistryException in ingest_data: {str(gre)}")
            error_response: G2PResponse = self.request_response_helper.construct_registry_error_response(gre, ingest_data_request)
            return error_response
        
        except Exception as e:
            _logger.error(f"Error in ingest_data: {str(e)}")
            error_response: G2PResponse = self.request_response_helper.construct_error_response(e, ingest_data_request)
            return error_response