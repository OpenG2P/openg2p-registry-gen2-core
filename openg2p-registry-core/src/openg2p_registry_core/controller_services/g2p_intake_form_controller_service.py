import logging
from openg2p_fastapi_common.service import BaseService

from ..models import G2PIntakeForm, G2PIntakeFormSectionPayload
from ..services import G2PIntakeFormService
from ..schemas import (
    SaveIntakeFormRequest, SaveIntakeFormRequestPayload,
    FinalizeIntakeFormRequest, FinalizeIntakeFormRequestPayload,
    ApproveRejectIntakeFormRequest, ApproveRejectIntakeFormRequestPayload,
    IntakeFormResponsePayload,
    SectionPayloadResponseItem,
    GetIntakeFormRequest, GetAllIntakeFormsRequest,
    SearchIntakeFormRequest,
)
from ..errors import G2PRegistryErrorCodes, G2PRegistryException

_logger = logging.getLogger('g2p-intake-form-controller-service')


class G2PIntakeFormControllerService(BaseService):

    async def save_intake_form_draft(self, save_intake_form_draft_request: SaveIntakeFormRequest) -> IntakeFormResponsePayload:
        payload: SaveIntakeFormRequestPayload = save_intake_form_draft_request.request_body.request_payload
        created_by = save_intake_form_draft_request.request_header.sender_app_mnemonic
        _logger.info(f"Saving intake form for register_id: {payload.register_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        g2p_intake_form: G2PIntakeForm = await g2p_intake_form_service.save_intake_form_draft(
            intake_form_request_payload=payload,
            created_by=created_by
        )
        return self._build_intake_form_response_payload(g2p_intake_form)

    async def finalize_intake_form(self, finalize_intake_form_request: FinalizeIntakeFormRequest) -> IntakeFormResponsePayload:
        payload: FinalizeIntakeFormRequestPayload = finalize_intake_form_request.request_body.request_payload
        intake_form_id = payload.intake_form_id
        finalized_by = finalize_intake_form_request.request_header.sender_app_mnemonic
        _logger.info(f"Saving final intake form with intake_form_id: {intake_form_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        g2p_intake_form: G2PIntakeForm = await g2p_intake_form_service.finalize_intake_form(
            intake_form_id=intake_form_id,
            finalized_by=finalized_by
        )
        return self._build_intake_form_response_payload(g2p_intake_form)

    async def approve_intake_form(self, approve_intake_form_request: ApproveRejectIntakeFormRequest) -> IntakeFormResponsePayload:
        payload: ApproveRejectIntakeFormRequestPayload = approve_intake_form_request.request_body.request_payload
        intake_form_id = payload.intake_form_id
        approved_by = approve_intake_form_request.request_header.sender_app_mnemonic
        _logger.info(f"Approving intake form with intake_form_id: {intake_form_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        g2p_intake_form: G2PIntakeForm = await g2p_intake_form_service.approve_intake_form(
            intake_form_id=intake_form_id,
            approved_by=approved_by
        )
        return self._build_intake_form_response_payload(g2p_intake_form)

    async def reject_intake_form(self, reject_intake_form_request: ApproveRejectIntakeFormRequest) -> IntakeFormResponsePayload:
        payload: ApproveRejectIntakeFormRequestPayload = reject_intake_form_request.request_body.request_payload
        intake_form_id = payload.intake_form_id
        rejected_by = reject_intake_form_request.request_header.sender_app_mnemonic
        _logger.info(f"Rejecting intake form with intake_form_id: {intake_form_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        g2p_intake_form: G2PIntakeForm = await g2p_intake_form_service.reject_intake_form(
            intake_form_id=intake_form_id,
            rejected_by=rejected_by
        )
        return self._build_intake_form_response_payload(g2p_intake_form)

    async def get_intake_form(self, get_intake_form_request: GetIntakeFormRequest) -> IntakeFormResponsePayload:
        intake_form_id = get_intake_form_request.request_body.request_payload.intake_form_id
        _logger.info(f"Getting intake form with intake_form_id: {intake_form_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        g2p_intake_form, section_payloads = await g2p_intake_form_service.get_intake_form(intake_form_id)
        return self._build_intake_form_response_payload(g2p_intake_form, section_payloads)

    async def get_all_intake_forms(self, get_all_intake_forms_request: GetAllIntakeFormsRequest) -> tuple[list[IntakeFormResponsePayload], int, int]:
        payload = get_all_intake_forms_request.request_body.request_payload
        pagination = get_all_intake_forms_request.request_body.pagination_request
        self._validate_pagination_request(pagination)
        register_id = payload.register_id
        _logger.info(f"Getting all paginated intake forms for register_id: {register_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        intake_forms_list, total_items = await g2p_intake_form_service.get_all_intake_forms(
            register_id=register_id,
            current_page=pagination.current_page,
            page_size=pagination.page_size,
            sort_by=pagination.sort_by,
            filter_by=pagination.filter_by
        )
        intake_form_response_payloads = [self._build_intake_form_response_payload(item) for item in intake_forms_list]
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return intake_form_response_payloads, total_items, number_of_pages

    async def search_in_intake_form(self, search_intake_form_request: SearchIntakeFormRequest) -> tuple[list[IntakeFormResponsePayload], int, int]:
        payload = search_intake_form_request.request_body.request_payload
        pagination = search_intake_form_request.request_body.pagination_request
        self._validate_pagination_request(pagination)
        register_id = payload.register_id
        _logger.info(f"Searching in intake form section payloads with search_text: {pagination.search_text} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        search_results_list, total_items = await g2p_intake_form_service.search_in_intake_form(
            register_id=register_id,
            search_text=pagination.search_text,
            current_page=pagination.current_page,
            page_size=pagination.page_size,
            sort_by=pagination.sort_by,
            filter_by=pagination.filter_by
        )
        intake_form_response_payloads = [self._build_intake_form_response_payload(item) for item in search_results_list]
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return intake_form_response_payloads, total_items, number_of_pages

    def _build_intake_form_response_payload(
        self,
        g2p_intake_form: G2PIntakeForm,
        section_payloads: list[G2PIntakeFormSectionPayload] | None = None
    ) -> IntakeFormResponsePayload:
        return IntakeFormResponsePayload(
            intake_form_id=g2p_intake_form.intake_form_id,
            register_id=g2p_intake_form.register_id,
            tab_id=g2p_intake_form.tab_id,
            foundational_id=g2p_intake_form.foundational_id,
            link_foundational_id=g2p_intake_form.link_foundational_id,
            intake_form_status=g2p_intake_form.intake_form_status,
            change_request_submission_status=g2p_intake_form.change_request_submission_status,
            change_request_id=g2p_intake_form.change_request_id,
            submission_no_of_attempts=g2p_intake_form.submission_no_of_attempts,
            submission_latest_datetime=str(g2p_intake_form.submission_latest_datetime) if g2p_intake_form.submission_latest_datetime else None,
            submission_latest_error_code=g2p_intake_form.submission_latest_error_code,
            no_of_verifications_required=g2p_intake_form.no_of_verifications_required,
            no_of_verifications_done=g2p_intake_form.no_of_verifications_done,
            approval_status=g2p_intake_form.approval_status,
            approved_by=g2p_intake_form.approved_by,
            approved_at=str(g2p_intake_form.approved_at) if g2p_intake_form.approved_at else None,
            created_by=g2p_intake_form.created_by,
            created_at=str(g2p_intake_form.created_at) if g2p_intake_form.created_at else None,
            last_updated_by=g2p_intake_form.last_updated_by,
            last_updated_at=str(g2p_intake_form.last_updated_at) if g2p_intake_form.last_updated_at else None,
            section_payloads=[
                SectionPayloadResponseItem(
                    section_id=section_payload.section_id,
                    payload_json=section_payload.intake_form_payload_json,
                )
                for section_payload in section_payloads
            ] if section_payloads is not None else None,
        )

    def _validate_pagination_request(self, pagination):
        if pagination is None:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1],
                message="pagination_request is required for this endpoint",
            )
