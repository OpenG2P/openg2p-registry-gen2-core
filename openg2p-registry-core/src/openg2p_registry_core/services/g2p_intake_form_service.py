import logging
from datetime import datetime

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.exc import IntegrityError

from ..models import (
    G2PIntakeForm,
    G2PIntakeFormSectionPayload,
    G2PRegisterUITab,
    IntakeFormStatusEnum,
    ChangeRequestStatusEnum,
    ApprovalStatusEnum,
)
from ..helpers import submission_reference_generator
from ..schemas import SaveSubmissionDraftRequestPayload, IntakeFormSubmissionsSummaryData
from ..errors import G2PRegistryErrorCodes, G2PRegistryException

_logger = logging.getLogger('g2p-intake-form-service')


class G2PIntakeFormService(BaseService):
    async def save_submission_draft(
        self,
        submission_request_payload: SaveSubmissionDraftRequestPayload,
        created_by: str
    ) -> G2PIntakeForm:
        """Create or update an intake form in DRAFT state and upsert section payloads."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)

        async with session_maker() as session:
            now = datetime.now()
            intake_form: G2PIntakeForm | None = None

            if submission_request_payload.submission_id:
                intake_form = await session.get(G2PIntakeForm, submission_request_payload.submission_id)
                if not intake_form:
                    self._raise_intake_form_not_found(submission_request_payload.submission_id)
                if intake_form.intake_form_status != IntakeFormStatusEnum.DRAFT.value:
                    self._raise_intake_form_invalid_state(
                        f"Intake form '{intake_form.submission_id}' can only be updated in DRAFT state"
                    )
            else:
                if not submission_request_payload.register_id:
                    self._raise_request_validation_error("register_id is required for creating a new intake form")
                if not submission_request_payload.tab_id:
                    self._raise_request_validation_error("tab_id is required for creating a new intake form")

                no_of_verifications_required = (
                    await session.execute(
                        select(G2PRegisterUITab.no_of_verifications_required).where(
                            G2PRegisterUITab.register_id == submission_request_payload.register_id,
                            G2PRegisterUITab.tab_id == submission_request_payload.tab_id,
                        ).limit(1)
                    )
                ).scalar_one_or_none() or 0

                intake_form = G2PIntakeForm(
                    register_id=submission_request_payload.register_id,
                    tab_id=submission_request_payload.tab_id,
                    foundational_id=submission_request_payload.foundational_id,
                    link_foundational_id=submission_request_payload.link_foundational_id,
                    submission_reference=submission_reference_generator.next_id(),
                    no_of_verifications_required=no_of_verifications_required,
                    created_by=created_by,
                    created_at=now,
                    last_updated_by=created_by,
                    last_updated_at=now,
                )
                session.add(intake_form)
                await session.flush()

            if submission_request_payload.register_id:
                intake_form.register_id = submission_request_payload.register_id
            if submission_request_payload.tab_id:
                intake_form.tab_id = submission_request_payload.tab_id
            intake_form.foundational_id = submission_request_payload.foundational_id
            intake_form.link_foundational_id = submission_request_payload.link_foundational_id
            if submission_request_payload.submission_id and submission_request_payload.no_of_verifications_required is not None:
                intake_form.no_of_verifications_required = submission_request_payload.no_of_verifications_required
            intake_form.last_updated_by = created_by
            intake_form.last_updated_at = now
            session.add(intake_form)

            if submission_request_payload.section_payloads:
                for section_payload in submission_request_payload.section_payloads:
                    row = await session.get(
                        G2PIntakeFormSectionPayload,
                        (intake_form.submission_id, section_payload.section_id),
                    )
                    if row:
                        row.submission_reference = intake_form.submission_reference
                        row.intake_form_payload_json = section_payload.intake_form_payload_json
                    else:
                        row = G2PIntakeFormSectionPayload(
                            submission_id=intake_form.submission_id,
                            section_id=section_payload.section_id,
                            submission_reference=intake_form.submission_reference,
                            intake_form_payload_json=section_payload.intake_form_payload_json,
                        )
                    session.add(row)

            await session.commit()
            await session.refresh(intake_form)
            return intake_form

    async def finalize_submission(
        self,
        submission_id: str,
        finalized_by: str = None
    ) -> G2PIntakeForm:
        """Move an intake form from DRAFT to FINAL and keep approval pending."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            intake_form = await session.get(G2PIntakeForm, submission_id)
            if not intake_form:
                self._raise_intake_form_not_found(submission_id)
            if intake_form.intake_form_status != IntakeFormStatusEnum.DRAFT.value:
                self._raise_intake_form_invalid_state(
                    f"Intake form '{submission_id}' must be in DRAFT state to be finalized"
                )

            section_count = (
                await session.execute(
                    select(func.count()).select_from(G2PIntakeFormSectionPayload).where(
                        G2PIntakeFormSectionPayload.submission_id == submission_id
                    )
                )
            ).scalar_one()
            if section_count <= 0:
                self._raise_request_validation_error(
                    f"Intake form '{submission_id}' has no section payloads and cannot be finalized"
                )

            now = datetime.now()
            intake_form.intake_form_status = IntakeFormStatusEnum.FINAL.value
            intake_form.approval_status = ApprovalStatusEnum.PENDING.value
            intake_form.last_updated_by = finalized_by or intake_form.last_updated_by
            intake_form.last_updated_at = now
            session.add(intake_form)

            await session.commit()
            await session.refresh(intake_form)
            return intake_form

    async def approve_submission(
        self,
        submission_id: str,
        approved_by: str
    ) -> G2PIntakeForm:
        """Approve a FINAL intake form and mark it ready for async CR submission."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            intake_form = await session.get(G2PIntakeForm, submission_id)
            if not intake_form:
                self._raise_intake_form_not_found(submission_id)
            if intake_form.intake_form_status != IntakeFormStatusEnum.FINAL.value:
                self._raise_intake_form_invalid_state(
                    f"Intake form '{submission_id}' must be FINAL before approval"
                )

            if (intake_form.no_of_verifications_done or 0) < (intake_form.no_of_verifications_required or 0):
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.INTAKE_FORM_VERIFICATIONS_PENDING.value[1],
                    message=G2PRegistryErrorCodes.INTAKE_FORM_VERIFICATIONS_PENDING.value[0],
                )

            now = datetime.now()
            intake_form.approval_status = ApprovalStatusEnum.APPROVED.value
            intake_form.approved_by = approved_by
            intake_form.approved_at = now
            intake_form.change_request_submission_status = ChangeRequestStatusEnum.PENDING.value
            intake_form.last_updated_by = approved_by
            intake_form.last_updated_at = now
            session.add(intake_form)

            await session.commit()
            await session.refresh(intake_form)
            return intake_form

    async def reject_submission(
        self,
        submission_id: str,
        rejected_by: str
    ) -> G2PIntakeForm:
        """Reject a FINAL intake form and mark it not applicable for async submission."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            intake_form = await session.get(G2PIntakeForm, submission_id)
            if not intake_form:
                self._raise_intake_form_not_found(submission_id)
            if intake_form.intake_form_status != IntakeFormStatusEnum.FINAL.value:
                self._raise_intake_form_invalid_state(
                    f"Intake form '{submission_id}' must be FINAL before rejection"
                )

            now = datetime.now()
            intake_form.approval_status = ApprovalStatusEnum.REJECTED.value
            intake_form.approved_by = rejected_by
            intake_form.approved_at = now
            intake_form.change_request_submission_status = ChangeRequestStatusEnum.NOT_APPLICABLE.value
            intake_form.last_updated_by = rejected_by
            intake_form.last_updated_at = now
            session.add(intake_form)

            await session.commit()
            await session.refresh(intake_form)
            return intake_form

    async def get_submission(
        self,
        submission_id: str
    ) -> tuple[G2PIntakeForm, list[G2PIntakeFormSectionPayload]]:
        """Fetch an intake form and its related section payload rows by submission_id."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            intake_form = await session.get(G2PIntakeForm, submission_id)
            if not intake_form:
                self._raise_intake_form_not_found(submission_id)
            section_payloads = (
                await session.execute(
                    select(G2PIntakeFormSectionPayload).where(
                        G2PIntakeFormSectionPayload.submission_id == submission_id
                    )
                )
            ).scalars().all()
            return intake_form, section_payloads

    async def get_intake_form_submissions_summary(self) -> IntakeFormSubmissionsSummaryData:
        """Fetch aggregate summary counts for intake form submissions."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            summary_query = select(
                func.count().label("total_submissions"),
                func.sum(
                    case((G2PIntakeForm.intake_form_status == IntakeFormStatusEnum.DRAFT.value, 1), else_=0)
                ).label("total_draft_submissions"),
                func.sum(
                    case((G2PIntakeForm.intake_form_status == IntakeFormStatusEnum.FINAL.value, 1), else_=0)
                ).label("total_final_submissions"),
                func.sum(
                    case(
                        (
                            (G2PIntakeForm.intake_form_status == IntakeFormStatusEnum.FINAL.value) &
                            (G2PIntakeForm.approval_status == ApprovalStatusEnum.PENDING.value),
                            1,
                        ),
                        else_=0,
                    )
                ).label("total_approval_pending_submissions"),
                func.sum(
                    case(
                        (
                            (G2PIntakeForm.change_request_id.is_not(None)) &
                            (G2PIntakeForm.change_request_id != ""),
                            1,
                        ),
                        else_=0,
                    )
                ).label("total_change_request_created_submissions"),
                func.sum(
                    case((G2PIntakeForm.approval_status == ApprovalStatusEnum.APPROVED.value, 1), else_=0)
                ).label("total_approved_submissions"),
                func.sum(
                    case((G2PIntakeForm.approval_status == ApprovalStatusEnum.REJECTED.value, 1), else_=0)
                ).label("total_rejected_submissions"),
            ).select_from(G2PIntakeForm)

            row = (await session.execute(summary_query)).one()
            return IntakeFormSubmissionsSummaryData(
                total_submissions=row.total_submissions or 0,
                total_draft_submissions=row.total_draft_submissions or 0,
                total_final_submissions=row.total_final_submissions or 0,
                total_approval_pending_submissions=row.total_approval_pending_submissions or 0,
                total_change_request_created_submissions=row.total_change_request_created_submissions or 0,
                total_approved_submissions=row.total_approved_submissions or 0,
                total_rejected_submissions=row.total_rejected_submissions or 0,
            )

    async def search_in_submission(
        self,
        register_id: str | None,
        tab_id: str | None,
        search_text: str | None,
        current_page: int,
        page_size: int,
        sort_by: str | None = None,
        filter_by=None
    ) -> tuple[list[G2PIntakeForm], int]:
        """
        Full-text search in G2PIntakeFormSectionPayload.intake_form_json_text.
        Returns full G2PIntakeForm objects.
        Returns (search_result_list, total_count).
        """
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            conditions = []
            if register_id:
                conditions.append(G2PIntakeForm.register_id == register_id)
            if tab_id:
                conditions.append(G2PIntakeForm.tab_id == tab_id)
            if search_text:
                conditions.append(G2PIntakeFormSectionPayload.intake_form_json_text.ilike(f"%{search_text}%"))

            query = (
                select(G2PIntakeForm)
                .join(
                    G2PIntakeFormSectionPayload,
                    G2PIntakeForm.submission_id == G2PIntakeFormSectionPayload.submission_id,
                )
                .where(*conditions)
            )
            query = self._apply_sort(query, sort_by)
            joined_results = (await session.execute(query)).scalars().all()

            deduped: list[G2PIntakeForm] = []
            seen_ids: set[str] = set()
            for intake_form in joined_results:
                if intake_form.submission_id in seen_ids:
                    continue
                seen_ids.add(intake_form.submission_id)
                deduped.append(intake_form)

            total_items = len(deduped)
            start = (current_page - 1) * page_size
            end = start + page_size
            return deduped[start:end], total_items

    def _apply_sort(self, query, sort_by: str | None):
        if not sort_by:
            return query.order_by(G2PIntakeForm.created_at.desc())

        sort_field = sort_by
        sort_desc = False
        if sort_by.startswith("-"):
            sort_desc = True
            sort_field = sort_by[1:]
        elif ":" in sort_by:
            parts = sort_by.split(":", 1)
            sort_field = parts[0]
            sort_desc = parts[1].lower() == "desc"

        if not hasattr(G2PIntakeForm, sort_field):
            _logger.warning(f"Invalid sort field '{sort_field}' for intake form query. Using default sort.")
            return query.order_by(G2PIntakeForm.created_at.desc())

        sort_column = getattr(G2PIntakeForm, sort_field)
        return query.order_by(sort_column.desc() if sort_desc else sort_column.asc())

    def _raise_intake_form_not_found(self, submission_id: str):
        raise G2PRegistryException(
            code=G2PRegistryErrorCodes.INTAKE_FORM_NOT_FOUND.value[1],
            message=f"{G2PRegistryErrorCodes.INTAKE_FORM_NOT_FOUND.value[0]}: {submission_id}",
        )

    def _raise_intake_form_invalid_state(self, message: str):
        raise G2PRegistryException(
            code=G2PRegistryErrorCodes.INTAKE_FORM_INVALID_STATE.value[1],
            message=message,
        )

    def _raise_request_validation_error(self, message: str):
        raise G2PRegistryException(
            code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1],
            message=message,
        )
