import logging
import importlib
from openg2p_fastapi_common.service import BaseService

from openg2p_registry_core.models import G2PRegisterChangeLog

from ..services import G2PRegisterService, G2PRegisterDomainService
from ..schemas import (
    ChangeLogRequest, ChangeLogRequestPayload, ChangeLogResponsePayload,
    NumberOfPendingChangeLogsData, NumberOfCrossRegisterChangesData,
    CrossRegisterChangeLogData, ChangeLogData,
    VerificationData, AddVerificationPayload,
    GetNumberOfPendingChangeLogsRequest, GetNumberOfCrossRegisterChangesRequest,
    GetCrossRegisterChangesRequest,
    GetChangeLogsRequest, GetChangeLogRequest,
    GetVerificationsRequest, AddVerificationRequest,
)

_logger = logging.getLogger('g2p-register-changelog-controller-service')


class G2PRegisterChangelogControllerService(BaseService):

    async def create_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponsePayload:
        _logger.info("Creating change log through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        change_log_request_payload: ChangeLogRequestPayload = change_log_request.request_body.request_payload

        module = importlib.import_module("openg2p_registry_extensions.register_domain.factory")
        domain_factory_class_name = "G2PRegisterDomainFactory"
        g2p_registry_domain_factory = getattr(module, domain_factory_class_name).get_component()
        domain_service: G2PRegisterDomainService = g2p_registry_domain_factory.get_domain_service(change_log_request_payload.register_mnemonic)
        print(f"Validating domain attributes for register mnemonic: {change_log_request_payload.register_mnemonic}")
        await domain_service.validate_domain_attributes(change_log_request_payload)

        g2p_register_change_log: G2PRegisterChangeLog = await g2p_register_service.create_change_log(
            change_log_request_payload=change_log_request_payload,
            source_partner_id=change_log_request.request_header.sender_app_mnemonic
        )

        change_log_response_payload: ChangeLogResponsePayload = self._build_change_log_response_payload(change_log_request_payload, g2p_register_change_log)

        return change_log_response_payload

    async def approve_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponsePayload:
        change_log_id = change_log_request.request_body.request_payload.change_log_id
        _logger.info(f"Approving change log with change_log_id: {change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        g2p_register_change_log: G2PRegisterChangeLog = await g2p_register_service.approve_change_log(change_log_id)
        change_log_response_payload: ChangeLogResponsePayload = self._build_change_log_response_payload(None, g2p_register_change_log)
        return change_log_response_payload

    async def reject_change_log(self, change_log_request: ChangeLogRequest) -> ChangeLogResponsePayload:
        change_log_id = change_log_request.request_body.request_payload.change_log_id
        rejection_reason: str = getattr(change_log_request.request_body.request_payload, 'rejection_reason', None)
        _logger.info(f"Rejecting change log with change_log_id: {change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        g2p_register_change_log: G2PRegisterChangeLog = await g2p_register_service.reject_change_log(change_log_id, rejection_reason)
        change_log_response_payload: ChangeLogResponsePayload = self._build_change_log_response_payload(None, g2p_register_change_log)
        return change_log_response_payload

    async def get_number_of_pending_change_logs(self, get_number_of_pending_change_logs_request: GetNumberOfPendingChangeLogsRequest) -> NumberOfPendingChangeLogsData:
        subject_register_id = get_number_of_pending_change_logs_request.request_body.request_payload.subject_register_id
        subject_record_id = get_number_of_pending_change_logs_request.request_body.request_payload.subject_record_id
        tab_id = get_number_of_pending_change_logs_request.request_body.request_payload.tab_id
        _logger.info(f"Getting number of pending change logs for subject_register_id: {subject_register_id}, subject_record_id: {subject_record_id}, tab_id: {tab_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        number_of_pending_change_logs_data: NumberOfPendingChangeLogsData = await g2p_register_service.get_number_of_pending_change_logs(subject_register_id, subject_record_id, tab_id)
        return number_of_pending_change_logs_data

    async def get_number_of_cross_register_changes(self, get_number_of_cross_register_changes_request: GetNumberOfCrossRegisterChangesRequest) -> NumberOfCrossRegisterChangesData:
        subject_register_id = get_number_of_cross_register_changes_request.request_body.request_payload.subject_register_id
        subject_record_id = get_number_of_cross_register_changes_request.request_body.request_payload.subject_record_id
        _logger.info(f"Getting number of cross-register changes for subject_register_id: {subject_register_id}, subject_record_id: {subject_record_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        number_of_cross_register_changes_data: NumberOfCrossRegisterChangesData = await g2p_register_service.get_number_of_cross_register_changes(subject_register_id, subject_record_id)
        return number_of_cross_register_changes_data

    async def get_cross_register_changes(self, get_cross_register_changes_request: GetCrossRegisterChangesRequest) -> list[CrossRegisterChangeLogData]:
        subject_register_id = get_cross_register_changes_request.request_body.request_payload.subject_register_id
        subject_record_id = get_cross_register_changes_request.request_body.request_payload.subject_record_id
        _logger.info(f"Getting cross-register changes for subject_register_id: {subject_register_id}, subject_record_id: {subject_record_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        cross_register_changes: list[CrossRegisterChangeLogData] = await g2p_register_service.get_cross_register_changes(subject_register_id, subject_record_id)
        return cross_register_changes

    async def get_change_logs(self, get_change_logs_request: GetChangeLogsRequest) -> tuple[list[ChangeLogData], int, int]:
        payload = get_change_logs_request.request_body.request_payload
        pagination = get_change_logs_request.request_body.pagination_request
        subject_register_id = payload.subject_register_id
        subject_record_id = payload.subject_record_id
        tab_id = payload.tab_id
        _logger.info(f"Getting change logs for subject_register_id: {subject_register_id}, subject_record_id: {subject_record_id}, tab_id: {tab_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        change_logs_list, total_items = await g2p_register_service.get_change_logs(
            subject_register_id, subject_record_id, tab_id, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return change_logs_list, total_items, number_of_pages

    async def get_change_log(self, get_change_log_request: GetChangeLogRequest) -> ChangeLogData:
        change_log_id = get_change_log_request.request_body.request_payload.change_log_id
        _logger.info(f"Getting change log for change_log_id: {change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        change_log_data: ChangeLogData = await g2p_register_service.get_change_log(change_log_id)
        return change_log_data

    def _build_change_log_response_payload(self, change_log_request_payload: ChangeLogRequestPayload, g2p_register_change_log: G2PRegisterChangeLog) -> ChangeLogResponsePayload:
        return ChangeLogResponsePayload(
            register_id=change_log_request_payload.register_id if change_log_request_payload else g2p_register_change_log.register_id,
            tab_id=g2p_register_change_log.tab_id,
            section_id=change_log_request_payload.section_id if change_log_request_payload else g2p_register_change_log.section_id,
            section_register_id=change_log_request_payload.section_register_id if change_log_request_payload else g2p_register_change_log.section_register_id,
            no_of_verifications_required=g2p_register_change_log.no_of_verifications_required,
            no_of_verifications_done=g2p_register_change_log.no_of_verifications_done,
            approval_status=g2p_register_change_log.approval_status,
            change_log_id=g2p_register_change_log.change_log_id,
            internal_record_id=g2p_register_change_log.internal_record_id,
            created_by=g2p_register_change_log.created_by,
            created_at=str(g2p_register_change_log.created_at) if g2p_register_change_log.created_at else None,
            approved_by=g2p_register_change_log.approved_by,
            approved_at=str(g2p_register_change_log.approved_at) if g2p_register_change_log.approved_at else None
        )

    async def get_verifications_for_change_log(self, get_verifications_request: GetVerificationsRequest) -> tuple[list[VerificationData], int, int]:
        payload = get_verifications_request.request_body.request_payload
        pagination = get_verifications_request.request_body.pagination_request
        change_log_id = payload.change_log_id
        _logger.info(f"Getting verifications for change_log_id: {change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        verifications_list, total_items = await g2p_register_service.get_verifications_for_change_log(
            change_log_id, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return verifications_list, total_items, number_of_pages

    async def add_verification_for_change_log(self, add_verification_request: AddVerificationRequest) -> VerificationData:
        add_verification_payload: AddVerificationPayload = add_verification_request.request_body.request_payload
        _logger.info(f"Adding verification for change_log_id: {add_verification_payload.change_log_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        verification_data: VerificationData = await g2p_register_service.add_verification_for_change_log(add_verification_payload)
        return verification_data

