import logging
import importlib
import uuid
from collections import defaultdict
from datetime import datetime

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.exc import IntegrityError

from ..models import (
    G2PIntakeForm,
    G2PIntakeFormSectionPayload,
    G2PIntakeFormSectionDocuments,
    G2PRegisterChangeRequest,
    G2PRegisterChangeRequestPayload,
    G2PRegisterDefinition,
    G2PRegisterSection,
    G2PRegisterUITab,
    IntakeFormStatusEnum,
    ChangeRequestStatusEnum,
    ApprovalStatusEnum,
)
from ..helpers import submission_reference_generator
from ..schemas import (
    SaveSubmissionDraftRequestPayload,
    IntakeFormSubmissionsSummaryData,
    SectionPayloadResponseItem,
    IntakeFormDocumentPayload,
)
from .g2p_register_domain_service import G2PRegisterDomainService
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
                if intake_form.intake_form_status != IntakeFormStatusEnum.DRAFT.value:
                    self._raise_intake_form_invalid_state(
                        f"Intake form '{intake_form.submission_id}' can only be updated in DRAFT state"
                    )
            else:
                if not submission_request_payload.register_id or not submission_request_payload.tab_id:
                    self._raise_request_validation_error("register_id and tab_id are required for creating a new intake form")

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
                    edit_action=submission_request_payload.edit_action,
                    internal_record_id=submission_request_payload.internal_record_id,
                    created_by=created_by,
                    created_at=now,
                )
                session.add(intake_form)
            

            register_domain_service: G2PRegisterDomainService | None = await self._get_domain_service_for_register(
                submission_request_payload.register_id,
                session,
            )

            constructed_record_name = self._construct_record_name(
                submission_request_payload.section_payloads,
                register_domain_service
            )
            if submission_request_payload.foundational_id:
                intake_form.foundational_id = submission_request_payload.foundational_id
            if submission_request_payload.link_foundational_id:
                intake_form.link_foundational_id = submission_request_payload.link_foundational_id
            if submission_request_payload.edit_action:
                intake_form.edit_action = submission_request_payload.edit_action.value if hasattr(submission_request_payload.edit_action, 'value') else submission_request_payload.edit_action
            if submission_request_payload.internal_record_id:
                intake_form.internal_record_id = submission_request_payload.internal_record_id
            if submission_request_payload.section_payloads is not None:
                intake_form.record_name = constructed_record_name
            intake_form.last_updated_by = created_by
            intake_form.last_updated_at = now
            session.add(intake_form)

            if submission_request_payload.section_payloads:
                for section_payload in submission_request_payload.section_payloads:
                    row = await session.get(
                        G2PIntakeFormSectionPayload,
                        (intake_form.submission_id, section_payload.section_id),
                    )
                    register_id = await self._get_section_register_id_for_section(
                        section_payload.section_id,
                        session
                    )
                    register_domain_service: G2PRegisterDomainService | None = await self._get_domain_service_for_register(
                        register_id,
                        session,
                    )
                    constructed_search_text = self._construct_search_text(
                        section_payload.intake_form_section_payload,
                        register_domain_service,
                        constructed_record_name,
                        str(intake_form.submission_reference),
                    )
                    if not row:
                        row = G2PIntakeFormSectionPayload(
                            submission_id=intake_form.submission_id,
                            section_id=section_payload.section_id,
                        )
                    
                    row.intake_form_section_payload = section_payload.intake_form_section_payload
                    row.intake_form_section_text = constructed_search_text
                    session.add(row)

                    # Add documents
                    if section_payload.documents:
                        for doc in section_payload.documents:
                            doc_row = G2PIntakeFormSectionDocuments(
                                submission_id=intake_form.submission_id,
                                section_id=section_payload.section_id,
                                document_label=doc.document_label,
                                document_store_id=doc.document_store_id,
                            )
                            session.add(doc_row)

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
            now = datetime.now()
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
    ) -> tuple[G2PIntakeForm, list[SectionPayloadResponseItem]]:
        """Fetch an intake form and its related section payload rows by submission_id."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            intake_form = await session.get(G2PIntakeForm, submission_id)
            if not intake_form:
                self._raise_intake_form_not_found(submission_id)
            section_payload_rows = (
                await session.execute(
                    select(G2PIntakeFormSectionPayload).where(
                        G2PIntakeFormSectionPayload.submission_id == submission_id
                    )
                )
            ).scalars().all()

            section_ids = [section_payload.section_id for section_payload in section_payload_rows]
            section_map = {}
            if section_ids:
                sections = (
                    await session.execute(
                        select(G2PRegisterSection).where(G2PRegisterSection.section_id.in_(section_ids))
                    )
                ).scalars().all()
                section_map = {section.section_id: section for section in sections}

            # Fetch documents for this submission grouped by section_id
            documents_rows = (
                await session.execute(
                    select(G2PIntakeFormSectionDocuments).where(
                        G2PIntakeFormSectionDocuments.submission_id == submission_id
                    )
                )
            ).scalars().all()

            documents_by_section: dict[str, list[IntakeFormDocumentPayload]] = defaultdict(list)
            for doc in documents_rows:
                documents_by_section[doc.section_id].append(
                    IntakeFormDocumentPayload(
                        document_label=doc.document_label,
                        document_store_id=doc.document_store_id,
                    )
                )

            section_payloads = [
                SectionPayloadResponseItem(
                    section_id=section_payload.section_id,
                    section_register_id=section_map[section_payload.section_id].section_register_id,
                    is_list=section_map[section_payload.section_id].is_list,
                    records=section_payload.intake_form_section_payload,
                    documents=documents_by_section.get(section_payload.section_id),
                )
                for section_payload in section_payload_rows
                if section_payload.section_id in section_map
            ]
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
        Full-text search in G2PIntakeFormSectionPayload.intake_form_section_text.
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
                conditions.append(G2PIntakeFormSectionPayload.intake_form_section_text.ilike(f"%{search_text}%"))

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

    async def get_change_requests_for_submission(
        self,
        submission_id: str,
        current_page: int,
        page_size: int,
        sort_by: str | None = None,
        filter_by=None
    ) -> tuple[list[dict], int]:
        """Get paginated flattened change requests for a given submission_id."""
        _ = filter_by
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            conditions = [G2PRegisterChangeRequest.submission_id == submission_id]

            total_items = (
                await session.execute(
                    select(func.count()).select_from(G2PRegisterChangeRequest).where(*conditions)
                )
            ).scalar_one()

            query = select(
                G2PRegisterChangeRequest,
                G2PRegisterChangeRequestPayload,
            ).join(
                G2PRegisterChangeRequestPayload,
                G2PRegisterChangeRequest.change_request_id == G2PRegisterChangeRequestPayload.change_request_id,
            ).where(*conditions)
            query = self._apply_change_request_sort(query, sort_by)
            query = query.offset((current_page - 1) * page_size).limit(page_size)
            rows = (await session.execute(query)).all()

            change_requests_list: list[dict] = []
            for change_request, payload in rows:
                created_at_str = (
                    str(change_request.created_at.isoformat())
                    if change_request.created_at and hasattr(change_request.created_at, "isoformat")
                    else None
                )
                approved_at_str = (
                    str(change_request.approved_at.isoformat())
                    if change_request.approved_at and hasattr(change_request.approved_at, "isoformat")
                    else None
                )

                g2p_register_section: G2PRegisterSection = (
                    await session.execute(
                        select(G2PRegisterSection).where(
                            G2PRegisterSection.section_id == change_request.section_id
                        )
                    )
                ).scalar()

                change_request_data = {
                    "change_request_id": change_request.change_request_id,
                    "record_name": change_request.record_name,
                    "register_id": change_request.register_id,
                    "tab_id": change_request.tab_id,
                    "internal_record_id": change_request.internal_record_id,
                    "section_id": change_request.section_id,
                    "section_mnemonic": g2p_register_section.section_mnemonic if g2p_register_section else None,
                    "source_partner_id": change_request.source_partner_id,
                    "created_by": change_request.created_by,
                    "created_at": created_at_str,
                    "no_of_verifications_required": change_request.no_of_verifications_required,
                    "no_of_verifications_done": change_request.no_of_verifications_done,
                    "approval_status": change_request.approval_status,
                    "approved_by": change_request.approved_by,
                    "approved_at": approved_at_str,
                }

                change_payload = payload.change_payload if payload else {}
                if change_payload and isinstance(change_payload, dict):
                    for key, value in change_payload.items():
                        if key != "internal_record_id":
                            change_request_data[key] = value

                change_requests_list.append(change_request_data)

            return change_requests_list, total_items

    async def get_number_of_pending_change_requests_for_submission(self, submission_id: str) -> int:
        """Get number of pending change requests for a submission."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            total_items = (
                await session.execute(
                    select(func.count()).select_from(G2PRegisterChangeRequest).where(
                        (G2PRegisterChangeRequest.submission_id == submission_id) &
                        (G2PRegisterChangeRequest.approval_status == ApprovalStatusEnum.PENDING.value)
                    )
                )
            ).scalar_one()
            return total_items or 0

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

    def _apply_change_request_sort(self, query, sort_by: str | None):
        if not sort_by:
            return query.order_by(G2PRegisterChangeRequest.created_at.desc())

        sort_field = sort_by
        sort_desc = False
        if sort_by.startswith("-"):
            sort_desc = True
            sort_field = sort_by[1:]
        elif ":" in sort_by:
            parts = sort_by.split(":", 1)
            sort_field = parts[0]
            sort_desc = parts[1].lower() == "desc"

        if not hasattr(G2PRegisterChangeRequest, sort_field):
            _logger.warning(f"Invalid sort field '{sort_field}' for change request query. Using default sort.")
            return query.order_by(G2PRegisterChangeRequest.created_at.desc())

        sort_column = getattr(G2PRegisterChangeRequest, sort_field)
        return query.order_by(sort_column.desc() if sort_desc else sort_column.asc())

    async def _get_section_register_id_for_section(self, section_id: str, session) -> str | None:
        register_id = (
            await session.execute(
                select(G2PRegisterSection.section_register_id).where(G2PRegisterSection.section_id == section_id)
            )
        ).scalar_one_or_none()
        return register_id
    
    async def _get_domain_service_for_register(self, register_id: str, session) -> G2PRegisterDomainService | None:
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(G2PRegisterDefinition.register_id == register_id)
            )
        ).scalar()

        domain_service = self._get_domain_service_by_register_mnemonic(register_definition.register_mnemonic)
        return domain_service

    def _get_domain_service_by_register_mnemonic(self, register_mnemonic: str) -> G2PRegisterDomainService | None:
        try:
            module = importlib.import_module("openg2p_registry_extensions.register_domain.factory")
            domain_factory_class_name = "G2PRegisterDomainFactory"
            g2p_registry_domain_factory = getattr(module, domain_factory_class_name).get_component()
            return g2p_registry_domain_factory.get_domain_service(register_mnemonic)
        except Exception as error:
            _logger.warning(
                f"Unable to resolve domain service for register mnemonic '{register_mnemonic}': {error}"
            )
            return None

    def _construct_record_name(
        self,
        section_payloads: list,
        register_domain_service: G2PRegisterDomainService | None,
    ) -> str | None:
        if not section_payloads or not register_domain_service:
            return None

        for section_payload in section_payloads:
            payload_records = getattr(section_payload, "intake_form_section_payload", None) or []
            for payload_dict in payload_records:
                if not isinstance(payload_dict, dict):
                    continue
                try:
                    record_name = register_domain_service.construct_record_name(payload_dict)
                    if record_name:
                        return record_name
                except NotImplementedError:
                    _logger.info("construct_record_name not implemented for intake draft domain service.")
                    return None
                except Exception as error:
                    _logger.warning(f"Could not construct intake draft record_name: {error}")
        return None
    
    def _construct_search_text(
        self,
        section_payload,
        register_domain_service: G2PRegisterDomainService | None,
        *args,
    ) -> str:
        if not section_payload or not register_domain_service:
            return ""

        payload_records = section_payload if isinstance(section_payload, list) else [section_payload]
        search_tokens: list[str] = []

        for payload_dict in payload_records:
            if not isinstance(payload_dict, dict):
                continue
            try:
                search_text = register_domain_service.construct_search_text(payload_dict, list(args))
                if search_text:
                    search_tokens.append(search_text.strip())
            except NotImplementedError:
                _logger.info("construct_search_text not implemented for intake draft domain service.")
                return ""
            except Exception as error:
                _logger.warning(f"Could not construct intake draft search_text: {error}")

        return " ".join(search_tokens).strip()

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
