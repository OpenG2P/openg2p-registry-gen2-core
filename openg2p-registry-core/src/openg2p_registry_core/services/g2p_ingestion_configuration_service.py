import logging
import uuid
from datetime import datetime
import httpx

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select

from ..models import (
    IncomingPartner,
    IncomingModelSignaturePattern,
    IncomingModelSemanticPattern,
    IncomingTemplate,
    IncomingPayloadEnricher,
    DataModel,
    SubscriptionActivityLog,
)
from ..schemas import (
    IncomingPartnerPayload,
    IncomingPartnerUpdatePayload,
    IncomingPartnerData,
    IncomingModelSignaturePatternPayload,
    IncomingModelSignaturePatternUpdatePayload,
    IncomingModelSignaturePatternData,
    IncomingModelSemanticPatternPayload,
    IncomingModelSemanticPatternUpdatePayload,
    IncomingModelSemanticPatternData,
    IncomingTemplatePayload,
    IncomingTemplateUpdatePayload,
    IncomingTemplateData,
    IncomingPayloadEnricherPayload,
    IncomingPayloadEnricherUpdatePayload,
    IncomingPayloadEnricherData,
    DataModelPayload,
    DataModelUpdatePayload,
    DataModelData,
    SubscriptionActivityLogPayload,
    SubscriptionActivityLogData,
)
from ..errors import G2PRegistryErrorCodes, G2PRegistryException

_logger = logging.getLogger("g2p-ingestion-configuration-service")


class G2PIngestionConfigurationService(BaseService):

    async def create_incoming_partner(
        self, incoming_partner_payload: IncomingPartnerPayload
    ) -> IncomingPartnerData:
        """Create a new incoming partner"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Check if partner mnemonic already exists
            existing = await session.execute(
                select(IncomingPartner).where(
                    IncomingPartner.partner_mnemonic == incoming_partner_payload.partner_mnemonic
                )
            )
            if existing.scalar_one_or_none():
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.PARTNER_ALREADY_EXISTS.value[1],
                    message=G2PRegistryErrorCodes.PARTNER_ALREADY_EXISTS.value[0],
                )

            partner_id = incoming_partner_payload.partner_id or str(uuid.uuid4())
            incoming_partner = IncomingPartner(
                partner_id=partner_id,
                partner_mnemonic=incoming_partner_payload.partner_mnemonic,
                keymanager_reference_id=incoming_partner_payload.keymanager_reference_id,
                is_active=incoming_partner_payload.is_active,
            )
            session.add(incoming_partner)
            await session.commit()
            await session.refresh(incoming_partner)
            return IncomingPartnerData.model_validate(incoming_partner)

    async def get_incoming_partner(self, partner_id: str) -> IncomingPartnerData:
        """Get incoming partner by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            partner = await session.execute(
                select(IncomingPartner).where(IncomingPartner.partner_id == partner_id)
            )
            partner_obj = partner.scalar_one_or_none()
            if not partner_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.PARTNER_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.PARTNER_NOT_FOUND.value[0],
                )
            return IncomingPartnerData.model_validate(partner_obj)

    async def update_incoming_partner(
        self, partner_id: str, incoming_partner_payload: IncomingPartnerUpdatePayload
    ) -> IncomingPartnerData:
        """Update incoming partner - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            partner = await session.execute(
                select(IncomingPartner).where(IncomingPartner.partner_id == partner_id)
            )
            partner_obj = partner.scalar_one_or_none()
            if not partner_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.PARTNER_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.PARTNER_NOT_FOUND.value[0],
                )

            # Only update fields that are provided (not None)
            if incoming_partner_payload.partner_mnemonic is not None:
                partner_obj.partner_mnemonic = incoming_partner_payload.partner_mnemonic
            if incoming_partner_payload.keymanager_reference_id is not None:
                partner_obj.keymanager_reference_id = incoming_partner_payload.keymanager_reference_id
            if incoming_partner_payload.is_active is not None:
                partner_obj.is_active = incoming_partner_payload.is_active

            await session.commit()
            await session.refresh(partner_obj)
            return IncomingPartnerData.model_validate(partner_obj)

    async def delete_incoming_partner(self, partner_id: str) -> None:
        """Soft delete incoming partner"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            partner = await session.execute(
                select(IncomingPartner).where(IncomingPartner.partner_id == partner_id)
            )
            partner_obj = partner.scalar_one_or_none()
            if not partner_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.PARTNER_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.PARTNER_NOT_FOUND.value[0],
                )

            partner_obj.is_active = False
            await session.commit()

    async def get_all_incoming_partners(self) -> list[IncomingPartnerData]:
        """Get all incoming partners"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(IncomingPartner).order_by(IncomingPartner.partner_mnemonic)
            )
            partners = result.scalars().all()
            return [IncomingPartnerData.model_validate(partner) for partner in partners]

    async def create_signature_pattern(
        self, pattern_payload: IncomingModelSignaturePatternPayload
    ) -> IncomingModelSignaturePatternData:
        """Create a new signature pattern"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern_id = pattern_payload.signature_pattern_id or str(uuid.uuid4())
            pattern = IncomingModelSignaturePattern(
                signature_pattern_id=pattern_id,
                data_model_id=pattern_payload.data_model_id,
                key_path_for_sender=pattern_payload.key_path_for_sender,
                key_path_for_signature=pattern_payload.key_path_for_signature,
            )
            session.add(pattern)
            await session.commit()
            await session.refresh(pattern)
            return IncomingModelSignaturePatternData.model_validate(pattern)

    async def get_signature_pattern(
        self, signature_pattern_id: str
    ) -> IncomingModelSignaturePatternData:
        """Get signature pattern by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern = await session.execute(
                select(IncomingModelSignaturePattern).where(
                    IncomingModelSignaturePattern.signature_pattern_id == signature_pattern_id
                )
            )
            pattern_obj = pattern.scalar_one_or_none()
            if not pattern_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.PATTERN_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.PATTERN_NOT_FOUND.value[0],
                )
            return IncomingModelSignaturePatternData.model_validate(pattern_obj)

    async def update_signature_pattern(
        self, signature_pattern_id: str, pattern_payload: IncomingModelSignaturePatternUpdatePayload
    ) -> IncomingModelSignaturePatternData:
        """Update signature pattern - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern = await session.execute(
                select(IncomingModelSignaturePattern).where(
                    IncomingModelSignaturePattern.signature_pattern_id == signature_pattern_id
                )
            )
            pattern_obj = pattern.scalar_one_or_none()
            if not pattern_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.PATTERN_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.PATTERN_NOT_FOUND.value[0],
                )

            # Only update fields that are provided (not None)
            if pattern_payload.key_path_for_sender is not None:
                pattern_obj.key_path_for_sender = pattern_payload.key_path_for_sender
            if pattern_payload.key_path_for_signature is not None:
                pattern_obj.key_path_for_signature = pattern_payload.key_path_for_signature

            await session.commit()
            await session.refresh(pattern_obj)
            return IncomingModelSignaturePatternData.model_validate(pattern_obj)

    # IncomingModelSemanticPattern Methods
    async def create_semantic_pattern(
        self, pattern_payload: IncomingModelSemanticPatternPayload
    ) -> IncomingModelSemanticPatternData:
        """Create a new semantic pattern"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern_id = pattern_payload.semantic_pattern_id or str(uuid.uuid4())
            pattern = IncomingModelSemanticPattern(
                semantic_pattern_id=pattern_id,
                data_model_id=pattern_payload.data_model_id,
                register_id=pattern_payload.register_id,
                operation_id=pattern_payload.operation_id,
                pattern_for_register=pattern_payload.pattern_for_register,
                pattern_for_operation=pattern_payload.pattern_for_operation,
            )
            session.add(pattern)
            await session.commit()
            await session.refresh(pattern)
            return IncomingModelSemanticPatternData.model_validate(pattern)

    async def get_semantic_pattern(
        self, semantic_pattern_id: str
    ) -> IncomingModelSemanticPatternData:
        """Get semantic pattern by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern = await session.execute(
                select(IncomingModelSemanticPattern).where(
                    IncomingModelSemanticPattern.semantic_pattern_id == semantic_pattern_id
                )
            )
            pattern_obj = pattern.scalar_one_or_none()
            if not pattern_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.SEMANTIC_PATTERN_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.SEMANTIC_PATTERN_NOT_FOUND.value[0],
                )
            return IncomingModelSemanticPatternData.model_validate(pattern_obj)

    async def update_semantic_pattern(
        self, semantic_pattern_id: str, pattern_payload: IncomingModelSemanticPatternUpdatePayload
    ) -> IncomingModelSemanticPatternData:
        """Update semantic pattern - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern = await session.execute(
                select(IncomingModelSemanticPattern).where(
                    IncomingModelSemanticPattern.semantic_pattern_id == semantic_pattern_id
                )
            )
            pattern_obj = pattern.scalar_one_or_none()
            if not pattern_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.SEMANTIC_PATTERN_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.SEMANTIC_PATTERN_NOT_FOUND.value[0],
                )

            if pattern_payload.pattern_for_register is not None:
                pattern_obj.pattern_for_register = pattern_payload.pattern_for_register
            if pattern_payload.pattern_for_operation is not None:
                pattern_obj.pattern_for_operation = pattern_payload.pattern_for_operation

            await session.commit()
            await session.refresh(pattern_obj)
            return IncomingModelSemanticPatternData.model_validate(pattern_obj)

    # IncomingTemplate Methods
    async def create_template(
        self, template_payload: IncomingTemplatePayload
    ) -> IncomingTemplateData:
        """Create a new template"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template_id = template_payload.template_id or str(uuid.uuid4())
            template = IncomingTemplate(
                template_id=template_id,
                register_id=template_payload.register_id,
                operation_id=template_payload.operation_id,
                data_model_id=template_payload.data_model_id,
                template_file_id=template_payload.template_file_id,
            )
            session.add(template)
            await session.commit()
            await session.refresh(template)
            return IncomingTemplateData.model_validate(template)

    async def get_template(self, template_id: str) -> IncomingTemplateData:
        """Get template by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template = await session.execute(
                select(IncomingTemplate).where(IncomingTemplate.template_id == template_id)
            )
            template_obj = template.scalar_one_or_none()
            if not template_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.TEMPLATE_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.TEMPLATE_NOT_FOUND.value[0],
                )
            return IncomingTemplateData.model_validate(template_obj)

    async def update_template(
        self, template_id: str, template_payload: IncomingTemplateUpdatePayload
    ) -> IncomingTemplateData:
        """Update template - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template = await session.execute(
                select(IncomingTemplate).where(IncomingTemplate.template_id == template_id)
            )
            template_obj = template.scalar_one_or_none()
            if not template_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.TEMPLATE_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.TEMPLATE_NOT_FOUND.value[0],
                )

            if template_payload.template_file_id is not None:
                template_obj.template_file_id = template_payload.template_file_id

            await session.commit()
            await session.refresh(template_obj)
            return IncomingTemplateData.model_validate(template_obj)

    # IncomingPayloadEnricher Methods
    async def create_payload_enricher(
        self, enricher_payload: IncomingPayloadEnricherPayload
    ) -> IncomingPayloadEnricherData:
        """Create a new payload enricher"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            enricher_id = enricher_payload.incoming_factory_id or str(uuid.uuid4())
            enricher = IncomingPayloadEnricher(
                incoming_factory_id=enricher_id,
                data_model_id=enricher_payload.data_model_id,
                register_id=enricher_payload.register_id,
                operation_id=enricher_payload.operation_id,
                raw_payload_enricher_class=enricher_payload.raw_payload_enricher_class,
            )
            session.add(enricher)
            await session.commit()
            await session.refresh(enricher)
            return IncomingPayloadEnricherData.model_validate(enricher)

    async def get_payload_enricher(
        self, incoming_factory_id: str
    ) -> IncomingPayloadEnricherData:
        """Get payload enricher by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            enricher = await session.execute(
                select(IncomingPayloadEnricher).where(
                    IncomingPayloadEnricher.incoming_factory_id == incoming_factory_id
                )
            )
            enricher_obj = enricher.scalar_one_or_none()
            if not enricher_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.PAYLOAD_ENRICHER_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.PAYLOAD_ENRICHER_NOT_FOUND.value[0],
                )
            return IncomingPayloadEnricherData.model_validate(enricher_obj)

    async def update_payload_enricher(
        self, incoming_factory_id: str, enricher_payload: IncomingPayloadEnricherUpdatePayload
    ) -> IncomingPayloadEnricherData:
        """Update payload enricher - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            enricher = await session.execute(
                select(IncomingPayloadEnricher).where(
                    IncomingPayloadEnricher.incoming_factory_id == incoming_factory_id
                )
            )
            enricher_obj = enricher.scalar_one_or_none()
            if not enricher_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.PAYLOAD_ENRICHER_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.PAYLOAD_ENRICHER_NOT_FOUND.value[0],
                )

            if enricher_payload.raw_payload_enricher_class is not None:
                enricher_obj.raw_payload_enricher_class = enricher_payload.raw_payload_enricher_class

            await session.commit()
            await session.refresh(enricher_obj)
            return IncomingPayloadEnricherData.model_validate(enricher_obj)

    # DataModel Methods
    async def create_data_model(
        self, data_model_payload: DataModelPayload
    ) -> DataModelData:
        """Create a new data model"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Check if data model mnemonic already exists
            existing = await session.execute(
                select(DataModel).where(
                    DataModel.data_model_mnemonic == data_model_payload.data_model_mnemonic
                )
            )
            if existing.scalar_one_or_none():
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.DATA_MODEL_ALREADY_EXISTS.value[1],
                    message=G2PRegistryErrorCodes.DATA_MODEL_ALREADY_EXISTS.value[0],
                )

            data_model_id = data_model_payload.data_model_id or str(uuid.uuid4())
            data_model = DataModel(
                data_model_id=data_model_id,
                data_model_mnemonic=data_model_payload.data_model_mnemonic,
                pattern_for_data_model=data_model_payload.pattern_for_data_model,
                is_active=data_model_payload.is_active,
            )
            session.add(data_model)
            await session.commit()
            await session.refresh(data_model)
            return DataModelData.model_validate(data_model)

    async def get_data_model(self, data_model_id: str) -> DataModelData:
        """Get data model by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            data_model = await session.execute(
                select(DataModel).where(DataModel.data_model_id == data_model_id)
            )
            data_model_obj = data_model.scalar_one_or_none()
            if not data_model_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.DATA_MODEL_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.DATA_MODEL_NOT_FOUND.value[0],
                )
            return DataModelData.model_validate(data_model_obj)

    async def update_data_model(
        self, data_model_id: str, data_model_payload: DataModelUpdatePayload
    ) -> DataModelData:
        """Update data model - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            data_model = await session.execute(
                select(DataModel).where(DataModel.data_model_id == data_model_id)
            )
            data_model_obj = data_model.scalar_one_or_none()
            if not data_model_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.DATA_MODEL_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.DATA_MODEL_NOT_FOUND.value[0],
                )

            if data_model_payload.data_model_mnemonic is not None:
                data_model_obj.data_model_mnemonic = data_model_payload.data_model_mnemonic
            if data_model_payload.pattern_for_data_model is not None:
                data_model_obj.pattern_for_data_model = data_model_payload.pattern_for_data_model

            await session.commit()
            await session.refresh(data_model_obj)
            return DataModelData.model_validate(data_model_obj)

    # SubscriptionActivityLog Methods
    async def create_subscription_activity_log(
        self, subscription_activity_log_payload: SubscriptionActivityLogPayload
    ) -> SubscriptionActivityLogData:
        """Create a new subscription activity log after calling the subscription URL"""
        # Call the subscription URL with header and payload
        response_data = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    subscription_activity_log_payload.subscription_url,
                    headers=subscription_activity_log_payload.header or {},
                    json=subscription_activity_log_payload.payload or {},
                    timeout=30.0
                )
                response.raise_for_status()  # Raise exception for non-2xx status codes
                response_data = response.json() if response.text else None
        except Exception as error:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.SUBSCRIPTION_CALL_FAILED.value[1],
                message=f"Failed to call subscription URL: {str(error)}"
            )

        # Only store the activity log if the call was successful
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            activity_log = SubscriptionActivityLog(
                subscription_activity_log_id=str(uuid.uuid4()),
                is_unsubscribe=subscription_activity_log_payload.is_unsubscribe,
                description=subscription_activity_log_payload.description,
                partner_id=subscription_activity_log_payload.partner_id,
                subscription_url=subscription_activity_log_payload.subscription_url,
                registry_callback_url=subscription_activity_log_payload.registry_callback_url,
                header=subscription_activity_log_payload.header,
                payload=subscription_activity_log_payload.payload,
                response=response_data,
            )
            session.add(activity_log)
            await session.commit()
            await session.refresh(activity_log)
            return SubscriptionActivityLogData.model_validate(activity_log)

    async def get_subscription_activity_logs_by_partner(
        self, partner_id: str
    ) -> list[SubscriptionActivityLogData]:
        """Get all subscription activity logs for a partner"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(SubscriptionActivityLog).where(
                    SubscriptionActivityLog.partner_id == partner_id
                ).order_by(SubscriptionActivityLog.date_time.desc())
            )
            activity_logs = result.scalars().all()
            return [SubscriptionActivityLogData.model_validate(log) for log in activity_logs]

