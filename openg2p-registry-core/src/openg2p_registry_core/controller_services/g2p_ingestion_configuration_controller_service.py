import logging
from typing import Optional
from fastapi import UploadFile
from openg2p_fastapi_common.service import BaseService

from ..services import G2PIngestionConfigurationService, G2PTemplateService
from ..schemas import (
    IncomingModelKeyPathPayload,
    IncomingModelKeyPathData,
    IncomingModelKeyPathListData,
    IncomingModelSemanticPatternPayload,
    IncomingModelSemanticPatternUpdatePayload,
    IncomingModelSemanticPatternData,
    IncomingTemplatePayload,
    IncomingTemplateUpdatePayload,
    IncomingTemplateData,
    DataModelPayload,
    DataModelUpdatePayload,
    DataModelData,
    SubscriptionActivityLogPayload,
    SubscriptionActivityLogData,
)

_logger = logging.getLogger("g2p-ingestion-configuration-controller-service")


class G2PIngestionConfigurationControllerService(BaseService):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.g2p_ingestion_configuration_service = G2PIngestionConfigurationService.get_component()
        self.g2p_template_service = G2PTemplateService.get_component()

    # IncomingModelKeyPath Methods
    async def create_new_incoming_key_path(
        self, pattern_payload: IncomingModelKeyPathPayload
    ) -> IncomingModelKeyPathData:
        """Create a new incoming key path"""
        return await self.g2p_ingestion_configuration_service.create_new_incoming_key_path(
            pattern_payload
        )

    async def get_all_incoming_key_paths(self) -> list[IncomingModelKeyPathListData]:
        """Get all incoming key paths"""
        return await self.g2p_ingestion_configuration_service.get_all_incoming_key_paths()

    async def delete_incoming_key_path(self, key_path_id: str) -> None:
        """Delete incoming key path"""
        return await self.g2p_ingestion_configuration_service.delete_incoming_key_path(
            key_path_id
        )

    async def edit_key_path_for_message_id(
        self, key_path_id: str, keypath_for_message_id: str
    ) -> IncomingModelKeyPathData:
        """Edit key_path_for_message_id field"""
        return await self.g2p_ingestion_configuration_service.edit_key_path_for_message_id(
            key_path_id, keypath_for_message_id
        )

    async def edit_key_path_for_sender(
        self, key_path_id: str, key_path_for_sender: str
    ) -> IncomingModelKeyPathData:
        """Edit key_path_for_sender field"""
        return await self.g2p_ingestion_configuration_service.edit_key_path_for_sender(
            key_path_id, key_path_for_sender
        )

    async def edit_key_path_for_signature(
        self, key_path_id: str, key_path_for_signature: str
    ) -> IncomingModelKeyPathData:
        """Edit key_path_for_signature field"""
        return await self.g2p_ingestion_configuration_service.edit_key_path_for_signature(
            key_path_id, key_path_for_signature
        )

    async def edit_key_path_for_signature_payload(
        self, key_path_id: str, key_path_for_signature_payload: str
    ) -> IncomingModelKeyPathData:
        """Edit key_path_for_signature_payload field"""
        return await self.g2p_ingestion_configuration_service.edit_key_path_for_signature_payload(
            key_path_id, key_path_for_signature_payload
        )

    async def edit_is_list(
        self, key_path_id: str, is_list: bool
    ) -> IncomingModelKeyPathData:
        """Edit is_list field"""
        return await self.g2p_ingestion_configuration_service.edit_is_list(
            key_path_id, is_list
        )

    async def edit_key_path_for_list_elements(
        self, key_path_id: str, keypath_for_list_elements: str
    ) -> IncomingModelKeyPathData:
        """Edit keypath_for_list_elements field"""
        return await self.g2p_ingestion_configuration_service.edit_key_path_for_list_elements(
            key_path_id, keypath_for_list_elements
        )

    async def create_semantic_pattern(
        self, pattern_payload: IncomingModelSemanticPatternPayload
    ) -> IncomingModelSemanticPatternData:
        """Create a new semantic pattern"""
        return await self.g2p_ingestion_configuration_service.create_semantic_pattern(
            pattern_payload
        )

    async def get_semantic_pattern(
        self, semantic_pattern_id: str
    ) -> IncomingModelSemanticPatternData:
        """Get semantic pattern by ID"""
        return await self.g2p_ingestion_configuration_service.get_semantic_pattern(
            semantic_pattern_id
        )

    async def update_semantic_pattern(
        self, semantic_pattern_id: str, pattern_payload: IncomingModelSemanticPatternUpdatePayload
    ) -> IncomingModelSemanticPatternData:
        """Update semantic pattern"""
        return await self.g2p_ingestion_configuration_service.update_semantic_pattern(
            semantic_pattern_id, pattern_payload
        )

    async def create_template(
        self, template_payload: IncomingTemplatePayload, template_file: UploadFile
    ) -> IncomingTemplateData:
        """Create a new template"""
        return await self.g2p_template_service.create_incoming_template(
            template_payload, template_file
        )

    async def get_template(self, template_id: str) -> IncomingTemplateData:
        """Get template by ID"""
        return await self.g2p_template_service.get_incoming_template(template_id)

    async def update_template(
        self, template_update_payload: IncomingTemplateUpdatePayload, template_file: Optional[UploadFile] = None
    ) -> IncomingTemplateData:
        """Update template"""
        return await self.g2p_template_service.update_incoming_template(
            template_update_payload, template_file
        )

    async def delete_template(self, template_delete_payload: IncomingTemplateUpdatePayload) -> IncomingTemplateData:
        """Delete template"""
        return await self.g2p_template_service.delete_incoming_template(template_delete_payload.template_id)

    async def create_data_model(
        self, data_model_payload: DataModelPayload, response_template_file=None
    ) -> DataModelData:
        """Create a new data model"""
        return await self.g2p_ingestion_configuration_service.create_data_model(
            data_model_payload, response_template_file
        )

    async def get_data_model(self, data_model_id: str) -> DataModelData:
        """Get data model by ID"""
        return await self.g2p_ingestion_configuration_service.get_data_model(data_model_id)

    async def get_all_data_models(self) -> list[DataModelData]:
        """Get all data models"""
        return await self.g2p_ingestion_configuration_service.get_all_data_models()

    async def update_data_model(
        self, data_model_id: str, data_model_payload: DataModelUpdatePayload, response_template_file=None
    ) -> DataModelData:
        """Update data model"""
        return await self.g2p_ingestion_configuration_service.update_data_model(
            data_model_id, data_model_payload, response_template_file
        )

    async def delete_data_model(self, data_model_id: str) -> DataModelData:
        """Delete data model"""
        return await self.g2p_ingestion_configuration_service.delete_data_model(data_model_id)

    async def change_response_template_file(
        self, data_model_id: str, response_template_file=None
    ) -> DataModelData:
        """Change response template file for data model"""
        return await self.g2p_ingestion_configuration_service.change_response_template_file(
            data_model_id, response_template_file
        )

    async def change_active_status(
        self, data_model_id: str, is_active: bool
    ) -> DataModelData:
        """Change active status of data model"""
        return await self.g2p_ingestion_configuration_service.change_active_status(
            data_model_id, is_active
        )

    async def create_subscription_activity_log(
        self, subscription_activity_log_payload: SubscriptionActivityLogPayload
    ) -> SubscriptionActivityLogData:
        """Create a new subscription activity log"""
        return await self.g2p_ingestion_configuration_service.create_subscription_activity_log(
            subscription_activity_log_payload
        )

    async def get_subscription_activity_logs_by_partner(
        self, partner_id: str
    ) -> list[SubscriptionActivityLogData]:
        """Get all subscription activity logs for a partner"""
        return await self.g2p_ingestion_configuration_service.get_subscription_activity_logs_by_partner(
            partner_id
        )

