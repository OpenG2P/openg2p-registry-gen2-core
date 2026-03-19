import logging
from typing import Optional, Tuple, List

from openg2p_fastapi_common.service import BaseService

from sqlalchemy.ext.asyncio import AsyncSession
from ..models import G2PRegisterChangeRequest, G2PRegisterChangeRequestDocument, G2PRegisterDefinition, G2PRegisterSection
from ..schemas import ChangeRequestRequestPayload
from .g2p_register_service import G2PRegisterService

_logger = logging.getLogger("g2p-change-request-worker-service")


class G2PChangeRequestWorkerService(BaseService):

    async def create_change_request(
        self,
        change_request_request_payload: ChangeRequestRequestPayload,
        session: AsyncSession,
        source_partner_id: Optional[str] = None,
        submission_id: Optional[str] = None,
    ) -> G2PRegisterChangeRequest:
        g2p_register_service = G2PRegisterService.get_component()
        g2p_register_definition: G2PRegisterDefinition = await g2p_register_service.validate_register_definition(
            change_request_request_payload.register_id, session
        )
        g2p_register_section: G2PRegisterSection = await g2p_register_service.validate_section(
            change_request_request_payload.section_id, session
        )

        # Extract internal_record_id from change_payload if present
        # Note: For new record creation, internal_record_id may be a new UUID that doesn't exist yet
        # We don't validate internal_record_id existence here - it will be created when the change request is approved

        g2p_register_change_request: G2PRegisterChangeRequest = await g2p_register_service.construct_change_request(
            change_request_request_payload,
            g2p_register_section,
            g2p_register_definition.register_mnemonic,
            source_partner_id,
            submission_id,
        )

        session.add(g2p_register_change_request)
        # Add the payload object if it exists
        if hasattr(g2p_register_change_request, '_payload_to_add'):
            session.add(g2p_register_change_request._payload_to_add)

        # Add documents if provided
        if change_request_request_payload.documents:
            for doc in change_request_request_payload.documents:
                change_request_doc = G2PRegisterChangeRequestDocument(
                    change_request_id=g2p_register_change_request.change_request_id,
                    document_label=doc.document_label,
                    document_store_id=doc.document_store_id
                )
                session.add(change_request_doc)

        # Ensure `change_request_id` and relationship rows are persisted within the caller's transaction.
        await session.flush()
        await session.refresh(g2p_register_change_request)
        return g2p_register_change_request


    async def auto_approve_primary_master_section_change_request(self, change_request_id: str, session: AsyncSession) -> Tuple[G2PRegisterChangeRequest, str]:
        g2p_register_service = G2PRegisterService.get_component()
        change_request, subject_internal_record_id = await g2p_register_service.approve_primary_master_section_change_request(
            change_request_id=change_request_id,
            session=session,
            skip_verification=True,
        )
        _logger.info(f"Auto-approved primary master section change request: {change_request_id}")
        await session.refresh(change_request)
        return change_request, subject_internal_record_id

    async def auto_approve_non_primary_master_section_change_request(self, change_request_id: str, subject_internal_record_id: str, session: AsyncSession) -> G2PRegisterChangeRequest:
        g2p_register_service = G2PRegisterService.get_component()
        change_request = await g2p_register_service.approve_non_primary_master_section_change_request(
            change_request_id=change_request_id,
            subject_internal_record_id=subject_internal_record_id,
            session=session,
            skip_verification=True,
        )
        _logger.info(f"Auto-approved non-primary master section change request: {change_request_id}")
        await session.refresh(change_request)
        return change_request

    async def auto_approve_child_section_change_request(self, change_request_id: str, subject_internal_record_id: str, session: AsyncSession) -> G2PRegisterChangeRequest:
        g2p_register_service = G2PRegisterService.get_component()
        change_request = await g2p_register_service.approve_child_section_change_request(
            change_request_id=change_request_id,
            subject_internal_record_id=subject_internal_record_id,
            session=session,
            skip_verification=True,
        )
        _logger.info(f"Auto-approved child section change request: {change_request_id}")
        await session.refresh(change_request)
        return change_request

    async def auto_approve_change_requests_in_order(
        self,
        change_request_ids: List[str],
        session: AsyncSession,
        *,
        submission_id: Optional[str] = None,
        fallback_subject_internal_record_id: Optional[str] = None,
    ) -> tuple[Optional[str], int, Optional[str]]:
        """
        Approve change requests in dependency-safe order, using the provided session/transaction:
        1. primary master section(s)
        2. non-primary master section(s)
        3. child section(s)

        Returns: (subject_internal_record_id, approved_count, last_attempted_change_request_id)
        """
        approved_count = 0
        subject_internal_record_id: Optional[str] = None
        last_attempted_change_request_id: Optional[str] = None

        primary_master_ids: list[str] = []
        non_primary_master_ids: list[str] = []
        child_ids: list[str] = []

        # Classify by section type.
        for change_request_id in change_request_ids:
            cr: G2PRegisterChangeRequest | None = await session.get(G2PRegisterChangeRequest, change_request_id)
            if not cr:
                continue
            section: G2PRegisterSection | None = await session.get(G2PRegisterSection, cr.section_id)
            if not section:
                continue

            if section.is_primary_section and section.section_register_id == section.register_id:
                primary_master_ids.append(change_request_id)
            elif (not section.is_primary_section) and section.section_register_id == section.register_id:
                non_primary_master_ids.append(change_request_id)
            else:
                child_ids.append(change_request_id)

        if submission_id:
            _logger.info(
                "Auto-approving intake-form change requests in order: "
                f"submission_id={submission_id}, "
                f"primary_master={len(primary_master_ids)}, "
                f"non_primary_master={len(non_primary_master_ids)}, "
                f"child={len(child_ids)}"
            )

        # 1. Primary master sections (establishes subject_internal_record_id for ADD)
        # Necessary condition for ADD action, optional for UPDATE action
        for change_request_id in primary_master_ids:
            last_attempted_change_request_id = change_request_id
            _logger.info(
                "Auto-approving primary master section change request: "
                f"{change_request_id}" + (f", submission_id={submission_id}" if submission_id else "")
            )
            _, subject_internal_record_id = await self.auto_approve_primary_master_section_change_request(
                change_request_id=change_request_id, session=session
            )
            approved_count += 1

        subject_internal_record_id = subject_internal_record_id or fallback_subject_internal_record_id

        # 2. Non-primary master sections
        if non_primary_master_ids:
            if not subject_internal_record_id:
                raise Exception(
                    "subject_internal_record_id is required to approve non-primary master change requests "
                    "but could not be determined."
                )
            for change_request_id in non_primary_master_ids:
                last_attempted_change_request_id = change_request_id
                _logger.info(
                    "Auto-approving non-primary master section change request: "
                    f"{change_request_id}" + (f", submission_id={submission_id}" if submission_id else "")
                )
                await self.auto_approve_non_primary_master_section_change_request(
                    change_request_id=change_request_id,
                    subject_internal_record_id=subject_internal_record_id,
                    session=session,
                )
                approved_count += 1

        # 3. Child sections
        if child_ids:
            if not subject_internal_record_id:
                raise Exception(
                    "subject_internal_record_id is required to approve child section change requests "
                    "but could not be determined."
                )
            for change_request_id in child_ids:
                last_attempted_change_request_id = change_request_id
                _logger.info(
                    "Auto-approving child section change request: "
                    f"{change_request_id}" + (f", submission_id={submission_id}" if submission_id else "")
                )
                await self.auto_approve_child_section_change_request(
                    change_request_id=change_request_id,
                    subject_internal_record_id=subject_internal_record_id,
                    session=session,
                )
                approved_count += 1

        return subject_internal_record_id, approved_count, last_attempted_change_request_id