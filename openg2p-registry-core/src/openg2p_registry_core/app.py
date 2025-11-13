# ruff: noqa: E402
import asyncio
import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer as BaseInitializer
from .services import G2PRegisterDomainService, G2PRegisterService
from .controller_services import G2PRegisterControllerService
from .models import G2PRegisterDefinition, G2PRegisterOperation, G2PRegisterVerification, G2PRegisterChangeLog, G2PRegisterChangeLogDocuments


_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()
        
        G2PRegisterDomainService()
        G2PRegisterService()
        G2PRegisterControllerService()
      
    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            _logger.info("Migrating database")
            await G2PRegisterDefinition.create_migrate()
            await G2PRegisterOperation.create_migrate()
            await G2PRegisterVerification.create_migrate()
            await G2PRegisterChangeLog.create_migrate()
            await G2PRegisterChangeLogDocuments.create_migrate()

        asyncio.run(migrate())
