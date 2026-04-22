# ruff: noqa: E402
import asyncio
import logging

from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.utils.crypto import KeymanagerCryptoHelper

from .cache import init_cache
from .config import Settings
from .controller_services import (
    G2PDataModelControllerService,
    G2PAttributeControllerService,
    G2PDocumentControllerService,
    G2PIngestControllerService,
    G2PIngestionConfigurationControllerService,
    G2PIngestionDataControllerService,
    G2PIntakeFormControllerService,
    G2POutgestionConfigurationControllerService,
    G2PTemplateFileControllerService,
    G2PRegisterChangerequestControllerService,
    G2PChangeRequestCoreControllerService,
    G2PRegisterDataControllerService,
    G2PRegisterMetadataControllerService,
    G2PRegistryConfigurationControllerService,
    G2PRegistryThemeControllerService,
    G2PUIHelperControllerService,
    G2PVcConfigurationControllerService,
    G2PVerificationControllerService,
)
from .helpers import MinioClient, PatternMatcher, TemplateHelper
from .models import (
    DataModel,
    DeduplicationChangerequestResult,
    DeduplicationRegisterResult,
    G2PAttribute,
    G2PAttributeValue,
    G2PInputMechanism,
    G2PIntakeForm,
    G2PIntakeFormSectionDocuments,
    G2PIntakeFormSectionPayload,
    G2PRegisterChangeRequest,
    G2PRegisterChangeRequestDocument,
    G2PRegisterChangeRequestPayload,
    G2PRegisterDefinition,
    G2PRegisterDocumentHistory,
    G2PRegisterSchema,
    G2PRegisterSection,
    G2PRegisterSectionDocument,
    G2PRegisterUITab,
    G2PRegisterVerification,
    G2PRegistryConfiguration,
    G2PRegistryTheme,
    G2PRegistryThemeValue,
    G2PRegistryDocument,
    G2PRegistryVcConfiguration,
    IncomingClassifiedData,
    IncomingEnrichedTransformedData,
    IncomingModelKeyPath,
    IncomingModelSemanticPattern,
    IncomingRawData,
    IncomingRawDataPayload,
    IncomingTemplate,
    OutgoingRawData,
    OutgoingRawDataPayload,
    OutgoingTemplate,
    OutgoingTopic,
    OutgoingTransformedDataPayload,
    SubscriptionActivityLog,
    G2PFunctionalIdGenerationQueue
)
from .services import (
    G2PDataModelService,
    G2PAttributeService,
    G2PChangeRequestWorkerService,
    G2PIngestionConfigurationService,
    G2PIngestionDataService,
    G2PIngestService,
    G2PIntakeFormService,
    G2POutgestionConfigurationService,
    G2PRegisterDomainService,
    G2PRegisterHierarchicalService,
    G2PRegisterService,
    G2PRegisterVerificationService,
    G2PTemplateService,
    G2PTemplateFileService,
    G2PUIHelperService,
    G2PVcConfigurationService,
    G2PChangeRequestCoreService,
)

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
        TemplateHelper(
            _config.template_bucket_name
        )
        PatternMatcher()
        KeymanagerCryptoHelper()

        # Services
        G2PDataModelService()
        G2PRegisterDomainService()
        G2PIngestService()
        G2PRegisterService()
        G2PRegisterHierarchicalService()
        G2PIngestionConfigurationService()
        G2PIngestionDataService()
        G2POutgestionConfigurationService()
        G2PTemplateService()
        G2PTemplateFileService()
        G2PAttributeService()
        G2PVcConfigurationService()
        G2PUIHelperService()
        G2PIntakeFormService()
        G2PRegisterVerificationService()
        G2PChangeRequestCoreService()
        G2PChangeRequestWorkerService()

        # Controller Services
        G2PDataModelControllerService()
        G2PIngestControllerService()
        G2PRegisterDataControllerService()
        G2PRegisterChangerequestControllerService()
        G2PChangeRequestCoreControllerService()
        G2PRegisterMetadataControllerService()
        G2PIngestionConfigurationControllerService()
        G2PIngestionDataControllerService()
        G2POutgestionConfigurationControllerService()
        G2PDocumentControllerService()
        G2PTemplateFileControllerService()
        G2PRegistryConfigurationControllerService()
        G2PRegistryThemeControllerService()
        G2PAttributeControllerService()
        G2PVcConfigurationControllerService()
        G2PUIHelperControllerService()
        G2PIntakeFormControllerService()
        G2PVerificationControllerService()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            # Data Models
            await DataModel.create_migrate()

            # Register Models
            await G2PIntakeForm.create_migrate()
            await G2PRegisterUITab.create_migrate()
            await G2PRegisterSchema.create_migrate()
            await G2PRegisterSection.create_migrate()
            await G2PRegisterDefinition.create_migrate()
            await G2PRegisterVerification.create_migrate()
            await G2PRegisterChangeRequest.create_migrate()
            await G2PRegistryConfiguration.create_migrate()
            await G2PRegistryTheme.create_migrate()
            await G2PRegistryThemeValue.create_migrate()
            await G2PRegisterDocumentHistory.create_migrate()
            await G2PRegisterSectionDocument.create_migrate()
            await G2PIntakeFormSectionPayload.create_migrate()
            await G2PIntakeFormSectionDocuments.create_migrate()
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

            # Id Generation Queue Models
            await G2PFunctionalIdGenerationQueue.create_migrate()

        asyncio.run(migrate())
