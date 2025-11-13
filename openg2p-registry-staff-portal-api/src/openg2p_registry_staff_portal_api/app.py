# ruff: noqa: E402
import asyncio
import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_registry_extensions.app import Initializer as BaseInitializer

from .helpers import RequestResponseHelper
from .controllers import G2PRegisterController

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()
        
        RequestResponseHelper()

        G2PRegisterController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            _logger.info("Migrating database")
  
        asyncio.run(migrate())
