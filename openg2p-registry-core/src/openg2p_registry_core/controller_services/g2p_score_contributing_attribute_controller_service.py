import logging
from typing import Tuple

from sqlalchemy.ext.asyncio import async_sessionmaker

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.schemas import G2PPaginationResponse
from openg2p_fastapi_common.service import BaseService

from ..schemas import (
    CreateScoreContributingAttributeRequest,
    CreateScoreContributingAttributeResponsePayload,
    DeleteScoreContributingAttributeRequest,
    DeleteScoreContributingAttributeResponsePayload,
    GetAllScoreContributingAttributesRequest,
    GetAllScoreContributingAttributesResponsePayload,
    ScoreContributingAttributeInput,
    UpdateScoreContributingAttributeRequest,
    UpdateScoreContributingAttributeResponsePayload,
)
from ..services import G2PScoreComputeService

_logger = logging.getLogger("g2p-score-contributing-attribute-controller-service")


def _number_of_pages(*, total_items: int, page_size: int) -> int:
    if total_items <= 0:
        return 0
    if page_size <= 0:
        return 1
    return (total_items + page_size - 1) // page_size


class G2PScoreContributingAttributeControllerService(BaseService):
    async def get_score_contributing_attributes(
        self, request: GetAllScoreContributingAttributesRequest
    ) -> Tuple[GetAllScoreContributingAttributesResponsePayload, G2PPaginationResponse]:
        _logger.info("Listing score contributing attributes for definition (paginated)")
        p = request.request_body.request_payload

        svc = G2PScoreComputeService.get_component()
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            rows, total = await svc.get_score_contributing_attributes_for_definition(
                score_definition_id=p.score_definition_id,
                page_number=p.page_number,
                page_size=p.page_size,
                session=session,
            )

        pagination = G2PPaginationResponse(
            number_of_items=total,
            number_of_pages=_number_of_pages(total_items=total, page_size=p.page_size),
        )
        return (
            GetAllScoreContributingAttributesResponsePayload(contributing_attributes=rows),
            pagination,
        )

    async def create_score_contributing_attribute(
        self, request: CreateScoreContributingAttributeRequest
    ) -> CreateScoreContributingAttributeResponsePayload:
        _logger.info("Creating score contributing attribute")
        payload = request.request_body.request_payload
        attribute = ScoreContributingAttributeInput(
            attribute_name=payload.attribute_name,
            attribute_computation_required=payload.attribute_computation_required,
            attribute_computation_value=payload.attribute_computation_value,
            attribute_weightage=payload.attribute_weightage,
        )

        svc = G2PScoreComputeService.get_component()
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            row = await svc.create_score_contributing_attribute(
                score_definition_id=payload.score_definition_id,
                attribute=attribute,
                session=session,
            )
            await session.commit()

        return CreateScoreContributingAttributeResponsePayload(contributing_attribute=row)

    async def update_score_contributing_attribute(
        self, request: UpdateScoreContributingAttributeRequest
    ) -> UpdateScoreContributingAttributeResponsePayload:
        _logger.info("Updating score contributing attribute")
        p = request.request_body.request_payload

        svc = G2PScoreComputeService.get_component()
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            row = await svc.update_score_contributing_attribute(
                contributing_attribute_id=p.contributing_attribute_id,
                attribute_name=p.attribute_name,
                attribute_computation_required=p.attribute_computation_required,
                attribute_computation_value=p.attribute_computation_value,
                attribute_weightage=p.attribute_weightage,
                session=session,
            )
            await session.commit()

        return UpdateScoreContributingAttributeResponsePayload(contributing_attribute=row)

    async def delete_score_contributing_attribute(
        self, request: DeleteScoreContributingAttributeRequest
    ) -> DeleteScoreContributingAttributeResponsePayload:
        _logger.info("Deleting score contributing attribute")
        contributing_attribute_id = request.request_body.request_payload.contributing_attribute_id

        svc = G2PScoreComputeService.get_component()
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            deleted_id = await svc.delete_score_contributing_attribute(
                contributing_attribute_id=contributing_attribute_id,
                session=session,
            )
            await session.commit()

        return DeleteScoreContributingAttributeResponsePayload(contributing_attribute_id=deleted_id)
