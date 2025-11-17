# ruff: noqa: E402
import asyncio
import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer as BaseInitializer

from .models import G2PRegisterFarmer, G2PRegisterHistoryFarmer
from .factory import G2PRegisterDomainFactory
from .services import G2PRegisterFarmerDomainService

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()
        
        G2PRegisterFarmerDomainService()
        G2PRegisterDomainFactory()
      
    def migrate_database(self, args):

        async def migrate():
            _logger.info("Migrating database")
            await G2PRegisterFarmer.create_migrate()
            await G2PRegisterHistoryFarmer.create_migrate()

        asyncio.run(migrate())
