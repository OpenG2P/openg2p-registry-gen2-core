import logging
from typing import Any

from openg2p_fastapi_common.service import BaseService

from ..errors import G2PRegistryErrorCodes, G2PRegistryException
from ..helpers import AWEClientError, AweHelper
from ..schemas.awe_proxy import (
    ClaimAweTaskRequestPayload,
    GetAweRequestEventsRequestPayload,
    GetAweRequestRequestPayload,
    ListMyAweTasksRequestPayload,
    SubmitAweTaskDecisionRequestPayload,
)

_logger = logging.getLogger("g2p-awe-proxy-controller-service")


class G2PAweProxyControllerService(BaseService):
    @staticmethod
    def _wrap_awe_error(exc: AWEClientError) -> G2PRegistryException:
        return G2PRegistryException(
            code=G2PRegistryErrorCodes.AWE_REQUEST_FAILED.value[1],
            message=f"{G2PRegistryErrorCodes.AWE_REQUEST_FAILED.value[0]}: {exc.message}",
        )

    async def list_my_tasks(
        self,
        payload: ListMyAweTasksRequestPayload,
        *,
        bearer_token: str,
    ) -> dict[str, Any]:
        try:
            return await AweHelper.get_component().list_my_tasks(
                bearer_token,
                request_id=payload.request_id,
                status=payload.status,
                artifact_type=payload.artifact_type,
                policy_key=payload.policy_key,
                page=payload.page,
                page_size=payload.page_size,
            )
        except AWEClientError as exc:
            raise self._wrap_awe_error(exc) from exc

    async def submit_task_decision(
        self,
        payload: SubmitAweTaskDecisionRequestPayload,
        *,
        bearer_token: str,
    ) -> dict[str, Any]:
        try:
            return await AweHelper.get_component().submit_decision(
                bearer_token,
                payload.task_id,
                action=payload.action,
                comment=payload.comment,
                attachments_ref=payload.attachments_ref,
            )
        except AWEClientError as exc:
            raise self._wrap_awe_error(exc) from exc

    async def claim_task(
        self,
        payload: ClaimAweTaskRequestPayload,
        *,
        bearer_token: str,
    ) -> dict[str, Any]:
        try:
            return await AweHelper.get_component().claim_task(bearer_token, payload.task_id)
        except AWEClientError as exc:
            raise self._wrap_awe_error(exc) from exc

    async def get_request(
        self,
        payload: GetAweRequestRequestPayload,
        *,
        bearer_token: str,
    ) -> dict[str, Any]:
        try:
            return await AweHelper.get_component().get_request(bearer_token, payload.request_id)
        except AWEClientError as exc:
            raise self._wrap_awe_error(exc) from exc

    async def get_request_events(
        self,
        payload: GetAweRequestEventsRequestPayload,
        *,
        bearer_token: str,
    ) -> list[dict[str, Any]]:
        try:
            return await AweHelper.get_component().get_request_events(bearer_token, payload.request_id)
        except AWEClientError as exc:
            raise self._wrap_awe_error(exc) from exc
