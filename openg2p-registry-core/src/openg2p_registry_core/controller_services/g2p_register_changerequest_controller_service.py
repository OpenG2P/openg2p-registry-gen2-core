import logging
import importlib
from openg2p_fastapi_common.service import BaseService

from openg2p_registry_core.models import G2PRegisterChangeRequest

from ..services import G2PRegisterService, G2PRegisterDomainService
from ..schemas import (
    ChangeRequestRequest, ChangeRequestRequestPayload, ChangeRequestResponsePayload,
    NumberOfPendingChangeRequestsData, NumberOfCrossRegisterChangesData,
    CrossRegisterChangeRequestData, ChangeRequestData,
    VerificationData, AddVerificationPayload,
    GetNumberOfPendingChangeRequestsRequest, GetNumberOfCrossRegisterChangesRequest,
    GetCrossRegisterChangesRequest,
    GetChangeRequestsRequest, GetChangeRequestRequest,
    GetVerificationsRequest, AddVerificationRequest,
    GetChangeRequestSummaryDataRequest, ChangeRequestSummaryData
)

_logger = logging.getLogger('g2p-register-changerequest-controller-service')


class G2PRegisterChangerequestControllerService(BaseService):

    async def create_change_request(self, change_request_request: ChangeRequestRequest) -> ChangeRequestResponsePayload:
        _logger.info("Creating change request through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        change_request_request_payload: ChangeRequestRequestPayload = change_request_request.request_body.request_payload

        module = importlib.import_module("openg2p_registry_extensions.register_domain.factory")
        domain_factory_class_name = "G2PRegisterDomainFactory"
        g2p_registry_domain_factory = getattr(module, domain_factory_class_name).get_component()
        domain_service: G2PRegisterDomainService = g2p_registry_domain_factory.get_domain_service(change_request_request_payload.register_mnemonic)
        print(f"Validating domain attributes for register mnemonic: {change_request_request_payload.register_mnemonic}")
        await domain_service.validate_domain_attributes(change_request_request_payload)

        g2p_register_change_request: G2PRegisterChangeRequest = await g2p_register_service.create_change_request(
            change_request_request_payload=change_request_request_payload,
            source_partner_id=change_request_request.request_header.sender_app_mnemonic
        )

        change_request_response_payload: ChangeRequestResponsePayload = self._build_change_request_response_payload(change_request_request_payload, g2p_register_change_request)

        return change_request_response_payload

    async def approve_change_request(self, change_request_request: ChangeRequestRequest) -> ChangeRequestResponsePayload:
        change_request_id = change_request_request.request_body.request_payload.change_request_id
        _logger.info(f"Approving change request with change_request_id: {change_request_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        g2p_register_change_request: G2PRegisterChangeRequest = await g2p_register_service.approve_change_request(change_request_id)
        change_request_response_payload: ChangeRequestResponsePayload = self._build_change_request_response_payload(None, g2p_register_change_request)
        return change_request_response_payload

    async def reject_change_request(self, change_request_request: ChangeRequestRequest) -> ChangeRequestResponsePayload:
        change_request_id = change_request_request.request_body.request_payload.change_request_id
        rejection_reason: str = getattr(change_request_request.request_body.request_payload, 'rejection_reason', None)
        _logger.info(f"Rejecting change request with change_request_id: {change_request_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        g2p_register_change_request: G2PRegisterChangeRequest = await g2p_register_service.reject_change_request(change_request_id, rejection_reason)
        change_request_response_payload: ChangeRequestResponsePayload = self._build_change_request_response_payload(None, g2p_register_change_request)
        return change_request_response_payload

    async def get_number_of_pending_change_requests(self, get_number_of_pending_change_requests_request: GetNumberOfPendingChangeRequestsRequest) -> NumberOfPendingChangeRequestsData:
        subject_register_id = get_number_of_pending_change_requests_request.request_body.request_payload.subject_register_id
        subject_record_id = get_number_of_pending_change_requests_request.request_body.request_payload.subject_record_id
        tab_id = get_number_of_pending_change_requests_request.request_body.request_payload.tab_id
        _logger.info(f"Getting number of pending change requests for subject_register_id: {subject_register_id}, subject_record_id: {subject_record_id}, tab_id: {tab_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        number_of_pending_change_requests_data: NumberOfPendingChangeRequestsData = await g2p_register_service.get_number_of_pending_change_requests(subject_register_id, subject_record_id, tab_id)
        return number_of_pending_change_requests_data

    async def get_number_of_cross_register_changes(self, get_number_of_cross_register_changes_request: GetNumberOfCrossRegisterChangesRequest) -> NumberOfCrossRegisterChangesData:
        subject_register_id = get_number_of_cross_register_changes_request.request_body.request_payload.subject_register_id
        subject_record_id = get_number_of_cross_register_changes_request.request_body.request_payload.subject_record_id
        _logger.info(f"Getting number of cross-register changes for subject_register_id: {subject_register_id}, subject_record_id: {subject_record_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        number_of_cross_register_changes_data: NumberOfCrossRegisterChangesData = await g2p_register_service.get_number_of_cross_register_changes(subject_register_id, subject_record_id)
        return number_of_cross_register_changes_data

    async def get_cross_register_changes(self, get_cross_register_changes_request: GetCrossRegisterChangesRequest) -> list[CrossRegisterChangeRequestData]:
        subject_register_id = get_cross_register_changes_request.request_body.request_payload.subject_register_id
        subject_record_id = get_cross_register_changes_request.request_body.request_payload.subject_record_id
        _logger.info(f"Getting cross-register changes for subject_register_id: {subject_register_id}, subject_record_id: {subject_record_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        cross_register_changes: list[CrossRegisterChangeRequestData] = await g2p_register_service.get_cross_register_changes(subject_register_id, subject_record_id)
        return cross_register_changes

    async def get_change_requests(self, get_change_requests_request: GetChangeRequestsRequest) -> tuple[list[dict], int, int]:
        payload = get_change_requests_request.request_body.request_payload
        pagination = get_change_requests_request.request_body.pagination_request
        subject_register_id = payload.subject_register_id
        subject_record_id = payload.subject_record_id
        tab_id = payload.tab_id
        _logger.info(f"Getting change requests for subject_register_id: {subject_register_id}, subject_record_id: {subject_record_id}, tab_id: {tab_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        # Use flattened version to return change_payload fields at root level
        change_requests_list, total_items = await g2p_register_service.get_change_requests_flattened(
            subject_register_id, subject_record_id, tab_id, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return change_requests_list, total_items, number_of_pages

    async def get_change_request(self, get_change_request_request: GetChangeRequestRequest) -> ChangeRequestData:
        change_request_id = get_change_request_request.request_body.request_payload.change_request_id
        _logger.info(f"Getting change request for change_request_id: {change_request_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        change_request_data: ChangeRequestData = await g2p_register_service.get_change_request(change_request_id)
        return change_request_data

    def _build_change_request_response_payload(self, change_request_request_payload: ChangeRequestRequestPayload, g2p_register_change_request: G2PRegisterChangeRequest) -> ChangeRequestResponsePayload:
        return ChangeRequestResponsePayload(
            register_id=change_request_request_payload.register_id if change_request_request_payload else g2p_register_change_request.register_id,
            tab_id=g2p_register_change_request.tab_id,
            section_id=change_request_request_payload.section_id if change_request_request_payload else g2p_register_change_request.section_id,
            section_register_id=change_request_request_payload.section_register_id if change_request_request_payload else g2p_register_change_request.section_register_id,
            no_of_verifications_required=g2p_register_change_request.no_of_verifications_required,
            no_of_verifications_done=g2p_register_change_request.no_of_verifications_done,
            approval_status=g2p_register_change_request.approval_status,
            change_request_id=g2p_register_change_request.change_request_id,
            internal_record_id=g2p_register_change_request.internal_record_id,
            created_by=g2p_register_change_request.created_by,
            created_at=str(g2p_register_change_request.created_at) if g2p_register_change_request.created_at else None,
            approved_by=g2p_register_change_request.approved_by,
            approved_at=str(g2p_register_change_request.approved_at) if g2p_register_change_request.approved_at else None
        )

    async def get_verifications_for_change_request(self, get_verifications_request: GetVerificationsRequest) -> tuple[list[VerificationData], int, int]:
        payload = get_verifications_request.request_body.request_payload
        pagination = get_verifications_request.request_body.pagination_request
        change_request_id = payload.change_request_id
        _logger.info(f"Getting verifications for change_request_id: {change_request_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        verifications_list, total_items = await g2p_register_service.get_verifications_for_change_request(
            change_request_id, pagination.current_page, pagination.page_size, pagination.sort_by, pagination.filter_by
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return verifications_list, total_items, number_of_pages

    async def add_verification_for_change_request(self, add_verification_request: AddVerificationRequest) -> VerificationData:
        add_verification_payload: AddVerificationPayload = add_verification_request.request_body.request_payload
        _logger.info(f"Adding verification for change_request_id: {add_verification_payload.change_request_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        verification_data: VerificationData = await g2p_register_service.add_verification_for_change_request(add_verification_payload)
        return verification_data

    async def get_changerequest_summary_data(self, get_changerequest_summary_data_request: GetChangeRequestSummaryDataRequest) -> ChangeRequestSummaryData:
        _logger.info("Fetching changerequest summary data through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        changerequest_summary_data: ChangeRequestSummaryData = await g2p_register_service.get_changerequest_summary_data()
        return changerequest_summary_data
