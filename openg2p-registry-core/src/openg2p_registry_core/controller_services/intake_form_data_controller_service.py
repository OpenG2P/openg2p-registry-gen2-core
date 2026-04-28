import logging
import math

from openg2p_fastapi_common.service import BaseService

from ..schemas import (
    ApproveRejectSubmissionRequest,
    DeleteIntakeFormSubmissionRequest,
    FinalizeSubmissionRequest,
    GetSubmissionRequest,
    GetDeduplicationIntakeFormRegisterResultsRequest,
    GetDeduplicationIntakeFormIntakeFormResultsRequest,
    DeduplicationIntakeFormRegisterResultData,
    DeduplicationIntakeFormIntakeFormResultData,
    SaveIntakeFormSubmissionRequest,
    SearchInSubmissionRequest,
    SubmissionResponsePayload,
)
from ..services import G2PIntakeFormDataService

_logger = logging.getLogger("g2p-intake-form-data-controller-service")


class G2PIntakeFormDataControllerService(BaseService):
    async def save_intake_form_submission(
        self,
        request: SaveIntakeFormSubmissionRequest,
    ) -> SubmissionResponsePayload:
        payload = request.request_body.request_payload
        return await G2PIntakeFormDataService.get_component().save_intake_form_submission(
            submission_id=payload.submission_id,
            section_id=payload.section_id,
            section_payload=payload.section_payload,
            section_register_id=payload.section_register_id,
            form_id=payload.form_id,
            register_id=payload.register_id,
            created_by=payload.created_by or "Unknown",
        )

    async def finalize_intake_form_submission(
        self,
        request: FinalizeSubmissionRequest,
    ) -> SubmissionResponsePayload:
        payload = request.request_body.request_payload
        return await G2PIntakeFormDataService.get_component().finalize_submission(payload.submission_id)

    async def delete_intake_form_submission(
        self,
        request: DeleteIntakeFormSubmissionRequest,
    ) -> SubmissionResponsePayload:
        payload = request.request_body.request_payload
        return await G2PIntakeFormDataService.get_component().delete_submission(payload.submission_id)

    async def approve_intake_form_submission(
        self,
        request: ApproveRejectSubmissionRequest,
    ) -> SubmissionResponsePayload:
        payload = request.request_body.request_payload
        return await G2PIntakeFormDataService.get_component().approve_submission(
            payload.submission_id,
            payload.approved_by or "Unknown",
        )

    async def reject_intake_form_submission(
        self,
        request: ApproveRejectSubmissionRequest,
    ) -> SubmissionResponsePayload:
        payload = request.request_body.request_payload
        return await G2PIntakeFormDataService.get_component().reject_submission(
            payload.submission_id,
            payload.approved_by or "Unknown",
        )

    async def get_intake_form_submission(
        self,
        request: GetSubmissionRequest,
    ) -> SubmissionResponsePayload:
        payload = request.request_body.request_payload
        return await G2PIntakeFormDataService.get_component().get_intake_form_submission(
            payload.submission_id,
            payload.section_register_id,
            payload.register_id,
            payload.section_id,
        )

    async def search_in_intake_form_submissions(self, request: SearchInSubmissionRequest):
        payload = request.request_body.request_payload
        records, total_items = await G2PIntakeFormDataService.get_component().search_submissions(
            payload.register_id,
            payload.search_text,
            payload.current_page,
            payload.page_size,
            payload.sort_by,
            payload.filter_by,
        )
        return records, total_items, math.ceil(total_items / payload.page_size) if payload.page_size else 0

    async def get_deduplication_intake_form_register_results(
        self,
        request: GetDeduplicationIntakeFormRegisterResultsRequest,
    ) -> tuple[list[DeduplicationIntakeFormRegisterResultData], int, int]:
        payload = request.request_body.request_payload
        results, total_items = await G2PIntakeFormDataService.get_component().get_deduplication_intake_form_register_results(
            submission_id=payload.submission_id,
            current_page=payload.current_page,
            page_size=payload.page_size,
            sort_by=payload.sort_by,
            filter_by=payload.filter_by,
        )
        number_of_pages = math.ceil(total_items / payload.page_size) if payload.page_size and total_items > 0 else 0
        return results, total_items, number_of_pages

    async def get_deduplication_intake_form_intake_form_results(
        self,
        request: GetDeduplicationIntakeFormIntakeFormResultsRequest,
    ) -> tuple[list[DeduplicationIntakeFormIntakeFormResultData], int, int]:
        payload = request.request_body.request_payload
        results, total_items = await G2PIntakeFormDataService.get_component().get_deduplication_intake_form_intake_form_results(
            submission_id=payload.submission_id,
            current_page=payload.current_page,
            page_size=payload.page_size,
            sort_by=payload.sort_by,
            filter_by=payload.filter_by,
        )
        number_of_pages = math.ceil(total_items / payload.page_size) if payload.page_size and total_items > 0 else 0
        return results, total_items, number_of_pages
