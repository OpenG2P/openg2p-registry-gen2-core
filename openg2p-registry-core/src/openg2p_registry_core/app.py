# ruff: noqa: E402
import asyncio
import logging

from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.utils.crypto import KeymanagerCryptoHelper
from .services import (
    G2PRegisterDomainService,
    G2PRegisterService,
    G2PRegisterHierarchicalService,
    G2PIngestService,
    G2PIngestionConfigurationService,
    G2POutgestionConfigurationService,
    G2PTemplateService,
    G2PAttributeService,
    G2PIngestionDataService,
    G2PVcConfigurationService,
    G2PUIHelperService
)
from .controller_services import (
    G2PRegisterDataControllerService,
    G2PRegisterChangerequestControllerService,
    G2PRegisterMetadataControllerService,
    G2PIngestControllerService,
    G2PIngestionConfigurationControllerService,
    G2POutgestionConfigurationControllerService,
    G2PDocumentControllerService,
    G2PRegistryConfigurationControllerService,
    G2PAttributeControllerService,
    G2PIngestionDataControllerService,
    G2PVcConfigurationControllerService,
    G2PUIHelperControllerService
)
from .models import (
    DataModel,
    G2PRegisterUITab,
    G2PRegisterSchema,
    G2PRegistryConfiguration,
    G2PRegisterDocumentHistory,
    G2PRegisterDefinition,
    G2PRegisterSection,
    G2PRegisterVerification,
    G2PRegisterChangeRequest,
    G2PRegisterChangeRequestPayload,
    G2PRegisterChangeRequestDocument,
    IncomingClassifiedData,
    IncomingEnrichedTransformedData,
    IncomingRawData,
    IncomingRawDataPayload,
    IncomingModelSemanticPattern,
    IncomingModelKeyPath,
    IncomingTemplate,
    OutgoingTopic,
    OutgoingTemplate,
    OutgoingRawData,
    OutgoingRawDataPayload,
    OutgoingTransformedDataPayload,
    G2PRegisterSectionDocument,
    SubscriptionActivityLog,
    G2PApplication,
    G2PApplicationSectionPayload,
    DeduplicationRegisterResult,
    DeduplicationChangerequestResult,
    G2PAttribute,
    G2PAttributeValue,
    G2PRegistryDocument,
    G2PRegistryVcConfiguration,
    G2PInputMechanism
)

from .helpers import PatternMatcher, TemplateHelper, MinioClient
from .cache import init_cache

from .config import Settings

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()

        # Cache
        init_cache()

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
        G2PRegisterHierarchicalService()
        G2PRegisterDomainService()
        G2PIngestionConfigurationService()
        G2PIngestionDataService()
        G2POutgestionConfigurationService()
        G2PTemplateService()
        G2PAttributeService()
        G2PVcConfigurationService()
        G2PUIHelperService()

        # Controller Services
        G2PIngestControllerService()
        G2PRegisterDataControllerService()
        G2PRegisterChangerequestControllerService()
        G2PRegisterMetadataControllerService()
        G2PIngestionConfigurationControllerService()
        G2PIngestionDataControllerService()
        G2POutgestionConfigurationControllerService()
        G2PDocumentControllerService()
        G2PRegistryConfigurationControllerService()
        G2PAttributeControllerService()
        G2PVcConfigurationControllerService()
        G2PUIHelperControllerService()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            # Data Models
            await DataModel.create_migrate()

            # Register Models
            await G2PApplication.create_migrate()
            await G2PRegisterUITab.create_migrate()
            await G2PRegisterSchema.create_migrate()
            await G2PRegisterSection.create_migrate()
            await G2PRegisterDefinition.create_migrate()
            await G2PRegisterVerification.create_migrate()
            await G2PRegisterChangeRequest.create_migrate()
            await G2PRegistryConfiguration.create_migrate()
            await G2PRegisterDocumentHistory.create_migrate()
            await G2PRegisterSectionDocument.create_migrate()
            await G2PApplicationSectionPayload.create_migrate()
            await G2PRegisterChangeRequestPayload.create_migrate()
            await G2PRegisterChangeRequestDocument.create_migrate()
            await G2PRegistryDocument.create_migrate()

            # Deduplication Models
            await DeduplicationRegisterResult.create_migrate()
            await DeduplicationChangerequestResult.create_migrate()

            # Incoming Models (IncomingPartner removed - now in master-data-db)
            await IncomingRawData.create_migrate()
            await IncomingTemplate.create_migrate()
            await IncomingModelKeyPath.create_migrate()
            await IncomingRawDataPayload.create_migrate()
            await IncomingClassifiedData.create_migrate()
            await SubscriptionActivityLog.create_migrate()
            await IncomingModelSemanticPattern.create_migrate()
            await IncomingEnrichedTransformedData.create_migrate()

            # Outgoing Models
            await OutgoingTopic.create_migrate()
            await OutgoingRawData.create_migrate()
            await OutgoingTemplate.create_migrate()
            await OutgoingRawDataPayload.create_migrate()
            await OutgoingTransformedDataPayload.create_migrate()

            # Attribute Models
            await G2PAttribute.create_migrate()
            await G2PAttributeValue.create_migrate()

            # VC Configuration Models
            await G2PInputMechanism.create_migrate()
            await G2PRegistryVcConfiguration.create_migrate()

        asyncio.run(migrate())
