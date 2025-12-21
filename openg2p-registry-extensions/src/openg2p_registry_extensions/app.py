# ruff: noqa: E402
import asyncio
import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_registry_core.app import Initializer as CoreInitializer

from .register_domain.models import (
    G2PRegisterFarmer,
    G2PRegisterHistoryFarmer,
    G2PRegisterFamily,
    G2PRegisterHistoryFamily,
    G2PRegisterFamilyMember,
    G2PRegisterHistoryFamilyMember,
    G2PRegisterHousehold,
    G2PRegisterHistoryHousehold,
    G2PRegisterAsset,
    G2PRegisterHistoryAsset,
)
from .register_domain.factory import G2PRegisterDomainFactory
from .register_domain.services import G2PRegisterFarmerDomainService

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()
        CoreInitializer().initialize()

        G2PRegisterFarmerDomainService()
        G2PRegisterDomainFactory()

    def migrate_database(self, args):

        async def migrate():
            _logger.info("Migrating extensions database")
            await G2PRegisterFarmer.create_migrate()
            await G2PRegisterHistoryFarmer.create_migrate()

            await G2PRegisterFamily.create_migrate()
            await G2PRegisterHistoryFamily.create_migrate()

            await G2PRegisterFamilyMember.create_migrate()
            await G2PRegisterHistoryFamilyMember.create_migrate()

            await G2PRegisterHousehold.create_migrate()
            await G2PRegisterHistoryHousehold.create_migrate()

            await G2PRegisterAsset.create_migrate()
            await G2PRegisterHistoryAsset.create_migrate()

        asyncio.run(migrate())
