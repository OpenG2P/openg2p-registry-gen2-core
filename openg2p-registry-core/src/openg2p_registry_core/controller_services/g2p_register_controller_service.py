import logging
from openg2p_fastapi_common.service import BaseService

from openg2p_registry_core.models import G2PRegisterChangeLog
from openg2p_registry_extensions.factory import G2PRegisterFactory

from ..services import G2PRegisterService
from ..schemas import ChangeLogRequest, ChangeLogPayload

_logger = logging.getLogger('g2p-register-controller-service')

class G2PRegisterControllerService(BaseService):
    
    async def create_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogPayload:
        _logger.info("Creating change log through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        change_log_payload: ChangeLogPayload = change_log_request.request_body.request_payload

        g2p_registry_factory = G2PRegisterFactory.get_component()
        implementation_service: G2PRegisterService = g2p_registry_factory.get_implementation_service(change_log_payload.register_mnemonic)
        await implementation_service.validate_change_log(change_log_payload)

        g2p_register_change_log: G2PRegisterChangeLog = await g2p_register_service.create_change_log(change_log_request)

        change_log_payload.change_log_id = g2p_register_change_log.change_log_id
        change_log_payload.approval_status = g2p_register_change_log.approval_status
        change_log_payload.no_of_verifications_required = g2p_register_change_log.no_of_verifications_required
        change_log_payload.no_of_verifications_done = g2p_register_change_log.no_of_verifications_done
        change_log_payload.internal_record_id = g2p_register_change_log.internal_record_id
        change_log_payload.created_by = g2p_register_change_log.created_by
        change_log_payload.created_at = str(g2p_register_change_log.created_at)
        change_log_payload.approved_by = g2p_register_change_log.approved_by
        change_log_payload.approved_at = str(g2p_register_change_log.approved_at) if g2p_register_change_log.approved_at else None

        return change_log_payload
