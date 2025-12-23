# ruff: noqa: E402
import asyncio
import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_registry_core.app import Initializer as CoreInitializer
from openg2p_registry_extensions.app import Initializer as ExtensionsInitializer

from .helpers import RequestResponseHelper
from .controllers import G2PRegisterDataController, G2PRegisterChangerequestController, G2PRegisterSummaryController, G2PRegisterMetadataController, IngestionConfigurationController, OutgestionConfigurationController

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        CoreInitializer().initialize()
        ExtensionsInitializer().initialize()
        
        RequestResponseHelper()

        G2PRegisterDataController().post_init()
        G2PRegisterChangerequestController().post_init()
        G2PRegisterSummaryController().post_init()
        G2PRegisterMetadataController().post_init()
        IngestionConfigurationController().post_init()
        OutgestionConfigurationController().post_init()

    def migrate_database(self, args):
        _logger.info("Starting database migration")

        CoreInitializer().get_component().migrate_database(args)
        ExtensionsInitializer().get_component().migrate_database(args)

        _logger.info("Database migration completed")
