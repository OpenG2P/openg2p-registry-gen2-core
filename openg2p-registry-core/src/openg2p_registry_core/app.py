# ruff: noqa: E402
import asyncio
import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.utils.crypto import KeymanagerCryptoHelper
from .services import G2PRegisterDomainService, G2PRegisterService, G2PPartnerService
from .controller_services import (
    G2PRegisterControllerService,
    G2PPartnerControllerService,
)
from .models import (
    DataModel,
    G2PRegisterDefinition,
    G2PRegisterOperation,
    G2PRegisterVerification,
    G2PRegisterChangeLog,
    G2PRegisterChangeLogDocuments,
    IncomingClassifiedData,
    IncomingEnrichedTransformedData,
    IncomingRawData,
    IncomingRawDataPayload,
    IncomingPayloadEnricher,
    IncomingModelSemanticPattern,
    IncomingModelSignaturePattern,
    IncomingPartner,
    IncomingTemplate,
)
from .helpers import PatternMatcher

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()

        # Helpers
        PatternMatcher()
        KeymanagerCryptoHelper()

        # Services
        G2PPartnerService()
        G2PRegisterService()
        G2PRegisterDomainService()

        # Controller Services
        G2PPartnerControllerService()
        G2PRegisterControllerService()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            _logger.info("Migrating database")

            # Data Models
            await DataModel.create_migrate()

            # Register Models
            await G2PRegisterDefinition.create_migrate()
            await G2PRegisterOperation.create_migrate()
            await G2PRegisterVerification.create_migrate()
            await G2PRegisterChangeLog.create_migrate()
            await G2PRegisterChangeLogDocuments.create_migrate()

            # Incoming Models
            await IncomingPartner.create_migrate()
            await IncomingRawData.create_migrate()
            await IncomingTemplate.create_migrate()
            await IncomingRawDataPayload.create_migrate()
            await IncomingClassifiedData.create_migrate()
            await IncomingPayloadEnricher.create_migrate()
            await IncomingEnrichedTransformedData.create_migrate()
            await IncomingModelSemanticPattern.create_migrate()
            await IncomingModelSignaturePattern.create_migrate()

        asyncio.run(migrate())
