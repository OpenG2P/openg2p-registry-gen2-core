import logging
from openg2p_fastapi_common.service import BaseService

from ..models import G2PIntakeForm
from ..services import G2PIntakeFormService, G2PRegisterService
from ..schemas import (
    SaveSubmissionDraftRequest, SaveSubmissionDraftRequestPayload,
    FinalizeSubmissionRequest, FinalizeSubmissionRequestPayload,
    ApproveRejectSubmissionRequest, ApproveRejectSubmissionRequestPayload,
    SubmissionResponsePayload,
    SectionPayloadResponseItem,
    GetSubmissionRequest, GetIntakeFormSubmissionsSummaryRequest,
    SearchInSubmissionRequest, GetChangeRequestsForSubmissionRequest, GetNumberOfPendingChangeRequestsForSubmissionRequest,
    IntakeFormSubmissionsSummaryData,
    NumberOfPendingChangeRequestsForSubmissionData,
    GetIntakeFormsForRegisterRequest, GetIntakeFormMetadataRequest,
    RegisterUITabData, RegisterSectionData,
)
from ..errors import G2PRegistryErrorCodes, G2PRegistryException

_logger = logging.getLogger('g2p-intake-form-controller-service')


class G2PIntakeFormControllerService(BaseService):
    async def save_submission_draft(self, save_submission_draft_request: SaveSubmissionDraftRequest) -> SubmissionResponsePayload:
        payload: SaveSubmissionDraftRequestPayload = save_submission_draft_request.request_body.request_payload
        created_by = save_submission_draft_request.request_header.sender_app_mnemonic
        _logger.info(f"Saving intake form for register_id: {payload.register_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        g2p_intake_form: G2PIntakeForm = await g2p_intake_form_service.save_submission_draft(
            submission_request_payload=payload,
            created_by=created_by
        )
        return self._build_submission_response_payload(g2p_intake_form)

    async def finalize_submission(self, finalize_submission_request: FinalizeSubmissionRequest) -> SubmissionResponsePayload:
        payload: FinalizeSubmissionRequestPayload = finalize_submission_request.request_body.request_payload
        submission_id = payload.submission_id
        finalized_by = finalize_submission_request.request_header.sender_app_mnemonic
        _logger.info(f"Saving final intake form with submission_id: {submission_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        g2p_intake_form: G2PIntakeForm = await g2p_intake_form_service.finalize_submission(
            submission_id=submission_id,
            finalized_by=finalized_by
        )
        return self._build_submission_response_payload(g2p_intake_form)

    async def approve_submission(self, approve_submission_request: ApproveRejectSubmissionRequest) -> SubmissionResponsePayload:
        payload: ApproveRejectSubmissionRequestPayload = approve_submission_request.request_body.request_payload
        submission_id = payload.submission_id
        approved_by = approve_submission_request.request_header.sender_app_mnemonic
        _logger.info(f"Approving intake form with submission_id: {submission_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        g2p_intake_form: G2PIntakeForm = await g2p_intake_form_service.approve_submission(
            submission_id=submission_id,
            approved_by=approved_by
        )
        return self._build_submission_response_payload(g2p_intake_form)

    async def reject_submission(self, reject_submission_request: ApproveRejectSubmissionRequest) -> SubmissionResponsePayload:
        payload: ApproveRejectSubmissionRequestPayload = reject_submission_request.request_body.request_payload
        submission_id = payload.submission_id
        rejected_by = reject_submission_request.request_header.sender_app_mnemonic
        _logger.info(f"Rejecting intake form with submission_id: {submission_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        g2p_intake_form: G2PIntakeForm = await g2p_intake_form_service.reject_submission(
            submission_id=submission_id,
            rejected_by=rejected_by
        )
        return self._build_submission_response_payload(g2p_intake_form)

    async def get_submission(self, get_submission_request: GetSubmissionRequest) -> SubmissionResponsePayload:
        submission_id = get_submission_request.request_body.request_payload.submission_id
        _logger.info(f"Getting intake form with submission_id: {submission_id} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        g2p_intake_form, section_payloads = await g2p_intake_form_service.get_submission(submission_id)
        return self._build_submission_response_payload(g2p_intake_form, section_payloads)

    async def get_intake_form_submissions_summary(
        self, get_intake_form_submissions_summary_request: GetIntakeFormSubmissionsSummaryRequest
    ) -> IntakeFormSubmissionsSummaryData:
        _ = get_intake_form_submissions_summary_request
        _logger.info("Getting intake form submissions summary through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        return await g2p_intake_form_service.get_intake_form_submissions_summary()

    async def get_intake_forms_for_register(
        self, get_intake_forms_for_register_request: GetIntakeFormsForRegisterRequest
    ) -> tuple[list[RegisterUITabData], int, int]:
        register_id = get_intake_forms_for_register_request.request_body.request_payload.register_id
        pagination = get_intake_forms_for_register_request.request_body.pagination_request
        self._validate_pagination_request(pagination)
        _logger.info(f"Getting intake forms for register_id: {register_id} through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        intake_forms, total_items = await g2p_register_service.get_register_tabs(
            register_id=register_id,
            current_page=pagination.current_page,
            page_size=pagination.page_size,
            used_for_new_intake_form=True,
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return intake_forms, total_items, number_of_pages

    async def get_intake_form_metadata(
        self, get_intake_form_metadata_request: GetIntakeFormMetadataRequest
    ) -> tuple[list[RegisterSectionData], int, int]:
        payload = get_intake_form_metadata_request.request_body.request_payload
        pagination = get_intake_form_metadata_request.request_body.pagination_request
        self._validate_pagination_request(pagination)
        register_id = payload.register_id
        tab_id = payload.intake_form_id
        _logger.info(
            f"Getting intake form metadata for register_id: {register_id}, intake_form_id: {tab_id} through controller service"
        )
        g2p_register_service = G2PRegisterService.get_component()
        sections, total_items = await g2p_register_service.get_register_tab_sections(
            register_id=register_id,
            tab_id=tab_id,
            current_page=pagination.current_page,
            page_size=pagination.page_size,
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return sections, total_items, number_of_pages

    async def search_in_submission(self, search_in_submission_request: SearchInSubmissionRequest) -> tuple[list[SubmissionResponsePayload], int, int]:
        payload = search_in_submission_request.request_body.request_payload
        pagination = search_in_submission_request.request_body.pagination_request
        self._validate_pagination_request(pagination)
        register_id = payload.register_id
        tab_id = payload.tab_id
        _logger.info(f"Searching in intake form section payloads with search_text: {pagination.search_text} through controller service")
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        search_results_list, total_items = await g2p_intake_form_service.search_in_submission(
            register_id=register_id,
            tab_id=tab_id,
            search_text=pagination.search_text,
            current_page=pagination.current_page,
            page_size=pagination.page_size,
            sort_by=pagination.sort_by,
            filter_by=pagination.filter_by
        )
        submission_response_payloads = [self._build_submission_response_payload(item) for item in search_results_list]
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return submission_response_payloads, total_items, number_of_pages

    async def get_change_requests_for_submission(
        self, get_change_requests_for_submission_request: GetChangeRequestsForSubmissionRequest
    ) -> tuple[list[dict], int, int]:
        payload = get_change_requests_for_submission_request.request_body.request_payload
        pagination = get_change_requests_for_submission_request.request_body.pagination_request
        self._validate_pagination_request(pagination)

        _logger.info(
            f"Getting change requests for submission_id: {payload.submission_id} through controller service"
        )
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        change_requests, total_items = await g2p_intake_form_service.get_change_requests_for_submission(
            submission_id=payload.submission_id,
            current_page=pagination.current_page,
            page_size=pagination.page_size,
            sort_by=pagination.sort_by,
            filter_by=pagination.filter_by,
        )
        number_of_pages = (total_items + pagination.page_size - 1) // pagination.page_size if total_items > 0 else 0
        return change_requests, total_items, number_of_pages

    async def get_number_of_pending_change_requests_for_submission(
        self,
        get_number_of_pending_change_requests_for_submission_request: GetNumberOfPendingChangeRequestsForSubmissionRequest
    ) -> NumberOfPendingChangeRequestsForSubmissionData:
        submission_id = (
            get_number_of_pending_change_requests_for_submission_request.request_body.request_payload.submission_id
        )
        _logger.info(
            f"Getting number of pending change requests for submission_id: {submission_id} through controller service"
        )
        g2p_intake_form_service = G2PIntakeFormService.get_component()
        count = await g2p_intake_form_service.get_number_of_pending_change_requests_for_submission(submission_id)
        return NumberOfPendingChangeRequestsForSubmissionData(
            number_of_pending_change_requests=count
        )

    def _build_submission_response_payload(
        self,
        g2p_intake_form: G2PIntakeForm,
        section_payloads: list[SectionPayloadResponseItem] | None = None
    ) -> SubmissionResponsePayload:
        return SubmissionResponsePayload(
            submission_id=g2p_intake_form.submission_id,
            submission_reference=g2p_intake_form.submission_reference,
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
            section_payloads=section_payloads,
        )

    def _validate_pagination_request(self, pagination):
        if pagination is None:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1],
                message="pagination_request is required for this endpoint",
            )
