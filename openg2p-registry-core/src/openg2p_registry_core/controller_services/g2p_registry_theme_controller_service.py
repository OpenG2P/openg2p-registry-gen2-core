import logging

from openg2p_fastapi_common.service import BaseService

from ..schemas import (
    CreateThemeRequest,
    GetAllThemesRequest,
    GetThemeValuesRequest,
    RegistryThemeData,
    RegistryThemeValueData,
    RemoveThemeRequest,
    ThemeOperationData,
    UpdateThemeValuesRequest,
)
from ..services import G2PRegisterService

_logger = logging.getLogger("g2p-registry-theme-controller-service")


class G2PRegistryThemeControllerService(BaseService):
    async def get_all_themes(self, get_request: GetAllThemesRequest) -> list[RegistryThemeData]:
        _logger.info("Fetching all themes through controller service")
        g2p_register_service = G2PRegisterService.get_component()
        return await g2p_register_service.get_all_themes()

    async def create_theme(self, create_request: CreateThemeRequest) -> ThemeOperationData:
        payload = create_request.request_body.request_payload
        _logger.info(f"Creating theme with mnemonic: {payload.theme_mnemonic}")
        g2p_register_service = G2PRegisterService.get_component()
        return await g2p_register_service.create_theme(
            theme_mnemonic=payload.theme_mnemonic,
            theme_values=payload.theme_values,
        )

    async def remove_theme(self, remove_request: RemoveThemeRequest) -> ThemeOperationData:
        payload = remove_request.request_body.request_payload
        _logger.info(f"Removing theme with id: {payload.theme_id}")
        g2p_register_service = G2PRegisterService.get_component()
        return await g2p_register_service.remove_theme(theme_id=payload.theme_id)

    async def update_theme_values(self, update_request: UpdateThemeValuesRequest) -> ThemeOperationData:
        payload = update_request.request_body.request_payload
        _logger.info(f"Updating theme values for theme id: {payload.theme_id}")
        g2p_register_service = G2PRegisterService.get_component()
        return await g2p_register_service.update_theme_values(
            theme_id=payload.theme_id,
            theme_attribute_values=payload.theme_attribute_values,
        )

    async def get_theme_values(self, get_request: GetThemeValuesRequest) -> list[RegistryThemeValueData]:
        payload = get_request.request_body.request_payload
        _logger.info(f"Fetching theme values for theme id: {payload.theme_id}")
        g2p_register_service = G2PRegisterService.get_component()
        return await g2p_register_service.get_theme_values(theme_id=payload.theme_id)
