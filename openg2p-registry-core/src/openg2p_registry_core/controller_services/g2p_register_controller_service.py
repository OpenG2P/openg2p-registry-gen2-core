import logging
from openg2p_fastapi_common.service import BaseService

from openg2p_registry_core.models import G2PRegisterChangeLog
import importlib

from ..services import G2PRegisterService, G2PRegisterDomainService
from ..schemas import ChangeLogRequest, ChangeLogPayload, RegisterSummaryData, RegisterData, ChildRegisterData

_logger = logging.getLogger('g2p-register-controller-service')

class G2PRegisterControllerService(BaseService):
    
    async def create_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogPayload:
        _logger.info("Creating change log through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        change_log_payload: ChangeLogPayload = change_log_request.request_body.request_payload

        module = importlib.import_module("openg2p_registry_extensions.factory")
        domain_factory_class_name = "G2PRegisterDomainFactory"
        g2p_registry_domain_factory = getattr(module, domain_factory_class_name).get_component()
        domain_service: G2PRegisterDomainService = g2p_registry_domain_factory.get_domain_service(change_log_payload.register_mnemonic)
        await domain_service.validate_domain_attributes(change_log_payload)

        g2p_register_change_log: G2PRegisterChangeLog = await g2p_register_service.create_change_log(change_log_request)

        enriched_change_log_payload: ChangeLogPayload = await self._enrich_change_log_payload(change_log_payload, g2p_register_change_log)
        
        return enriched_change_log_payload

    async def approve_change_log(self, change_log_id: str) -> ChangeLogPayload:

        g2p_register_service = G2PRegisterService.get_component()
        g2p_register_change_log: G2PRegisterChangeLog = await g2p_register_service.approve_change_log(change_log_id)
        change_log_payload = ChangeLogPayload()
        change_log: ChangeLogPayload = await self._enrich_change_log_payload(change_log_payload, g2p_register_change_log)
        return change_log

    async def reject_change_log(self, change_log_id: str) -> ChangeLogPayload:
        g2p_register_service = G2PRegisterService.get_component()
        g2p_register_change_log: G2PRegisterChangeLog = await g2p_register_service.reject_change_log(change_log_id)
        change_log_payload = ChangeLogPayload()
        change_log: ChangeLogPayload = await self._enrich_change_log_payload(change_log_payload, g2p_register_change_log)
        return change_log

    async def get_register_summary_data(self) -> list[RegisterSummaryData]:
        _logger.info("Fetching register summary data through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        register_summary_data_list: list[RegisterSummaryData] = await g2p_register_service.get_register_summary_data()
        return register_summary_data_list

    async def get_all_registers(self) -> list[RegisterData]:
        _logger.info("Fetching all registers through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        all_registers_list: list[RegisterData] = await g2p_register_service.get_all_registers()
        return all_registers_list

    async def get_child_registers(self, register_id: str) -> list[ChildRegisterData]:
        _logger.info(f"Fetching child registers for register_id: {register_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        child_registers_list: list[ChildRegisterData] = await g2p_register_service.get_child_registers(register_id)
        return child_registers_list

    async def _enrich_change_log_payload(self, change_log_payload: ChangeLogPayload , g2p_register_change_log: G2PRegisterChangeLog) -> ChangeLogPayload:
        
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