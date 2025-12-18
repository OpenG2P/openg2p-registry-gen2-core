# ruff: noqa: E402
import asyncio
import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.utils.crypto import KeymanagerCryptoHelper
from .services import (
    G2PRegisterDomainService,
    G2PRegisterService,
    G2PIngestService,
    G2PIngestionConfigurationService,
    G2POutgestionConfigurationService,
    G2PTemplateService,
)
from .controller_services import (
    G2PRegisterControllerService,
    G2PIngestControllerService,
    G2PIngestionConfigurationControllerService,
    G2POutgestionConfigurationControllerService,
)
from .models import (
    DataModel,
    G2PRegisterDefinition,
    G2PRegisterOperation,
    G2PRegisterVerification,
    G2PRegisterChangeLog,
    G2PRegisterChangeLogPayload,
    G2PRegisterChangeLogDocuments,
    IncomingClassifiedData,
    IncomingEnrichedTransformedData,
    IncomingRawData,
    IncomingRawDataPayload,
    IncomingPayloadEnricher,
    IncomingModelSemanticPattern,
    IncomingModelKeyPath,
    IncomingPartner,
    IncomingTemplate,
    OutgoingTopic,
    OutgoingTemplate,
    OutgoingRawData,
    OutgoingRawDataPayload,
    OutgoingTransformedDataPayload,
)
from .helpers import PatternMatcher, TemplateHelper, MinioClient

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()

        # Helpers
        MinioClient(
            _config.minio_endpoint,
            _config.minio_access_key,
            _config.minio_secret_key,
            _config.minio_secure,
            _config.minio_bucket_name,
        )
        TemplateHelper()
        PatternMatcher()
        KeymanagerCryptoHelper()

        # Services
        G2PIngestService()
        G2PRegisterService()
        G2PRegisterDomainService()
        G2PIngestionConfigurationService()
        G2POutgestionConfigurationService()
        G2PTemplateService()

        # Controller Services
        G2PIngestControllerService()
        G2PRegisterControllerService()
        G2PIngestionConfigurationControllerService()
        G2POutgestionConfigurationControllerService()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            # Data Models
            await DataModel.create_migrate()

            # Register Models
            await G2PRegisterDefinition.create_migrate()
            await G2PRegisterOperation.create_migrate()
            await G2PRegisterVerification.create_migrate()
            await G2PRegisterChangeLog.create_migrate()
            await G2PRegisterChangeLogPayload.create_migrate()
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
            await IncomingModelKeyPath.create_migrate()

            # Outgoing Models
            await OutgoingTopic.create_migrate()
            await OutgoingTemplate.create_migrate()
            await OutgoingRawData.create_migrate()
            await OutgoingRawDataPayload.create_migrate()
            await OutgoingTransformedDataPayload.create_migrate()
        
        asyncio.run(migrate())
