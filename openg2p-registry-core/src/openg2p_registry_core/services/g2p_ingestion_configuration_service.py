import logging
import uuid
from datetime import datetime
from typing import Optional, List
import httpx
from fastapi import UploadFile

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select

from ..models import (
    IncomingPartner,
    IncomingModelKeyPath,
    IncomingModelSemanticPattern,
    IncomingTemplate,
    DataModel,
    SubscriptionActivityLog,
)
from ..schemas import (
    IncomingPartnerPayload,
    IncomingPartnerUpdatePayload,
    IncomingPartnerData,
    IncomingModelKeyPathPayload,
    IncomingModelKeyPathUpdatePayload,
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
from .g2p_template_service import G2PTemplateService
from ..errors import G2PRegistryErrorCodes, G2PRegistryException
from ..helpers import MinioClient, TemplateHelper
from ..engine import get_engines

_logger = logging.getLogger("g2p-ingestion-configuration-service")


class G2PIngestionConfigurationService(BaseService):

    async def create_incoming_partner(
        self, incoming_partner_payload: IncomingPartnerPayload
    ) -> IncomingPartnerData:
        """Create a new incoming partner"""
        master_data_engine = get_engines().get("db_engine_master_data")
        session_maker = async_sessionmaker(master_data_engine, expire_on_commit=False)
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
        master_data_engine = get_engines().get("db_engine_master_data")
        session_maker = async_sessionmaker(master_data_engine, expire_on_commit=False)
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
        master_data_engine = get_engines().get("db_engine_master_data")
        session_maker = async_sessionmaker(master_data_engine, expire_on_commit=False)
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
        master_data_engine = get_engines().get("db_engine_master_data")
        session_maker = async_sessionmaker(master_data_engine, expire_on_commit=False)
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
        master_data_engine = get_engines().get("db_engine_master_data")
        session_maker = async_sessionmaker(master_data_engine, expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(IncomingPartner).order_by(IncomingPartner.partner_mnemonic)
            )
            partners = result.scalars().all()
            return [IncomingPartnerData.model_validate(partner) for partner in partners]

    # IncomingModelKeyPath Methods
    async def create_new_incoming_key_path(
        self, pattern_payload: IncomingModelKeyPathPayload
    ) -> IncomingModelKeyPathData:
        """Create a new incoming key path"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern_id = pattern_payload.key_path_id or str(uuid.uuid4())
            pattern = IncomingModelKeyPath(
                key_path_id=pattern_id,
                data_model_id=pattern_payload.data_model_id,
                key_path_for_message_id=pattern_payload.keypath_for_message_id,
                key_path_for_sender=pattern_payload.key_path_for_sender,
                key_path_for_signature=pattern_payload.key_path_for_signature,
                key_path_for_signature_payload=pattern_payload.key_path_for_signature_payload,
                is_list=pattern_payload.is_list,
                key_path_for_list_elements=pattern_payload.keypath_for_list_elements,
            )
            session.add(pattern)
            await session.commit()
            await session.refresh(pattern)
            return IncomingModelKeyPathData.model_validate(pattern)

    async def get_all_incoming_key_paths(self) -> list[IncomingModelKeyPathListData]:
        """Get all incoming key paths with data_model_mnemonic"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(IncomingModelKeyPath)
            )
            key_paths = result.scalars().all()

            # Build list with data_model_mnemonic
            key_path_list: list[IncomingModelKeyPathListData] = []
            for key_path in key_paths:
                # Get data model to retrieve mnemonic
                data_model_result = await session.execute(
                    select(DataModel).where(DataModel.data_model_id == key_path.data_model_id)
                )
                data_model = data_model_result.scalar_one_or_none()
                data_model_mnemonic = data_model.data_model_mnemonic if data_model else ""

                key_path_list.append(IncomingModelKeyPathListData(
                    key_path_id=key_path.key_path_id,
                    data_model_id=key_path.data_model_id,
                    data_model_mnemonic=data_model_mnemonic,
                    is_list=key_path.is_list,
                ))
            return key_path_list

    async def delete_incoming_key_path(self, key_path_id: str) -> None:
        """Delete incoming key path"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern = await session.execute(
                select(IncomingModelKeyPath).where(
                    IncomingModelKeyPath.key_path_id == key_path_id
                )
            )
            pattern_obj = pattern.scalar_one_or_none()
            if not pattern_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.PATTERN_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.PATTERN_NOT_FOUND.value[0],
                )
            await session.delete(pattern_obj)
            await session.commit()

    async def edit_key_path_for_message_id(
        self, key_path_id: str, keypath_for_message_id: str
    ) -> IncomingModelKeyPathData:
        """Edit key_path_for_message_id field"""
        return await self._update_incoming_key_path_field(
            key_path_id, "key_path_for_message_id", keypath_for_message_id
        )

    async def edit_key_path_for_sender(
        self, key_path_id: str, key_path_for_sender: str
    ) -> IncomingModelKeyPathData:
        """Edit key_path_for_sender field"""
        return await self._update_incoming_key_path_field(
            key_path_id, "key_path_for_sender", key_path_for_sender
        )

    async def edit_key_path_for_signature(
        self, key_path_id: str, key_path_for_signature: str
    ) -> IncomingModelKeyPathData:
        """Edit key_path_for_signature field"""
        return await self._update_incoming_key_path_field(
            key_path_id, "key_path_for_signature", key_path_for_signature
        )

    async def edit_key_path_for_signature_payload(
        self, key_path_id: str, key_path_for_signature_payload: str
    ) -> IncomingModelKeyPathData:
        """Edit key_path_for_signature_payload field"""
        return await self._update_incoming_key_path_field(
            key_path_id, "key_path_for_signature_payload", key_path_for_signature_payload
        )

    async def edit_is_list(
        self, key_path_id: str, is_list: bool
    ) -> IncomingModelKeyPathData:
        """Edit is_list field"""
        return await self._update_incoming_key_path_field(
            key_path_id, "is_list", is_list
        )

    async def edit_key_path_for_list_elements(
        self, key_path_id: str, keypath_for_list_elements: str
    ) -> IncomingModelKeyPathData:
        """Edit keypath_for_list_elements field"""
        return await self._update_incoming_key_path_field(
            key_path_id, "key_path_for_list_elements", keypath_for_list_elements
        )

    async def _update_incoming_key_path_field(
        self, key_path_id: str, field_name: str, field_value
    ) -> IncomingModelKeyPathData:
        """Helper method to update a single field on IncomingModelKeyPath"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern = await session.execute(
                select(IncomingModelKeyPath).where(
                    IncomingModelKeyPath.key_path_id == key_path_id
                )
            )
            pattern_obj = pattern.scalar_one_or_none()
            if not pattern_obj:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.PATTERN_NOT_FOUND.value[1],
                    message=G2PRegistryErrorCodes.PATTERN_NOT_FOUND.value[0],
                )

            setattr(pattern_obj, field_name, field_value)
            await session.commit()
            await session.refresh(pattern_obj)
            return IncomingModelKeyPathData.model_validate(pattern_obj)

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
                section_id=pattern_payload.section_id,
                pattern_for_register=pattern_payload.pattern_for_register,
                pattern_for_section=pattern_payload.pattern_for_section,
                key_path_for_business_payload=pattern_payload.key_path_for_business_payload,
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
            if pattern_payload.pattern_for_section is not None:
                pattern_obj.pattern_for_section = pattern_payload.pattern_for_section
            if pattern_payload.key_path_for_business_payload is not None:
                pattern_obj.key_path_for_business_payload = pattern_payload.key_path_for_business_payload

            await session.commit()
            await session.refresh(pattern_obj)
            return IncomingModelSemanticPatternData.model_validate(pattern_obj)

    # IncomingTemplate Methods
    async def create_template(
        self, template_payload: IncomingTemplatePayload, template_file: UploadFile
    ) -> IncomingTemplateData:
        """Create a new template"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self._check_incoming_template_exists(session, template_payload)

            file_id: str = await self._upload_template_file(template_file, template_payload.template_file_id)

            template_id: str = template_payload.template_id or str(uuid.uuid4())
            template: IncomingTemplate = IncomingTemplate(
                template_id=template_id,
                register_id=template_payload.register_id,
                data_model_id=template_payload.data_model_id,
                template_file_id=file_id,
            )
            session.add(template)
            await session.commit()
            await session.refresh(template)
            return IncomingTemplateData.model_validate(template)

    async def get_template(self, template_id: str) -> IncomingTemplateData:
        """Get template by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template_obj: IncomingTemplate = await self._get_incoming_template(session, template_id)
            return IncomingTemplateData.model_validate(template_obj)

    async def update_template(
        self, template_update_payload: IncomingTemplateUpdatePayload, template_file: Optional[UploadFile] = None
    ) -> IncomingTemplateData:
        """Update template - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template_obj: IncomingTemplate = await self._get_incoming_template(
                session, template_update_payload.template_id
            )

            if template_file:
                template_obj.template_file_id = await self._upload_template_file(
                    template_file, template_update_payload.template_file_id
                )

            await session.commit()
            await session.refresh(template_obj)
            return IncomingTemplateData.model_validate(template_obj)

    async def _get_incoming_template(self, session: AsyncSession, template_id: str) -> IncomingTemplate:
        """Get incoming template by ID - helper method"""
        if not template_id:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.INVALID_REQUEST.value[1],
                message=G2PRegistryErrorCodes.INVALID_REQUEST.value[0],
            )
        template = await session.execute(
            select(IncomingTemplate).where(IncomingTemplate.template_id == template_id)
        )
        template_obj: Optional[IncomingTemplate] = template.scalar_one_or_none()
        if not template_obj:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.TEMPLATE_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.TEMPLATE_NOT_FOUND.value[0],
            )
        return template_obj

    async def _check_incoming_template_exists(
        self, session: AsyncSession, template_payload: IncomingTemplatePayload
    ) -> None:
        """Check if template with same data_model_id, register_id, and section_id already exists"""
        if not template_payload.data_model_id or not template_payload.register_id or not template_payload.section_id:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.INVALID_REQUEST.value[1],
                message=G2PRegistryErrorCodes.INVALID_REQUEST.value[0],
            )
        existing_template = await session.execute(
            select(IncomingTemplate).where(
                IncomingTemplate.data_model_id == template_payload.data_model_id,
                IncomingTemplate.register_id == template_payload.register_id,
            )
        )
        existing_template_obj: Optional[IncomingTemplate] = existing_template.scalar_one_or_none()
        if existing_template_obj:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.TEMPLATE_ALREADY_EXISTS.value[1],
                message=G2PRegistryErrorCodes.TEMPLATE_ALREADY_EXISTS.value[0],
            )

    async def _upload_template_file(self, template_file: UploadFile, template_file_id: Optional[str]) -> str:
        """Upload template file to MinIO and return the file ID"""
        minio_client: MinioClient = MinioClient.get_component()
        template_helper: TemplateHelper = TemplateHelper.get_component()

        template_text: str = (await template_file.read()).decode("utf-8")
        file_id: str = template_helper.put_template(
            minio_client=minio_client,
            template_file_id=template_file_id,
            template=template_text
        )
        return file_id

    # DataModel Methods
    async def create_data_model(
        self, data_model_payload: DataModelPayload, response_template_file: Optional[UploadFile] = None
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

            response_template_file_id = None
            if response_template_file:
                response_template_file_id = await self._upload_template_file(response_template_file)

            data_model = DataModel(
                data_model_id=data_model_id,
                data_model_mnemonic=data_model_payload.data_model_mnemonic,
                pattern_for_data_model=data_model_payload.pattern_for_data_model,
                response_template_file_id=response_template_file_id,
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

    async def get_all_data_models(self) -> List[DataModelData]:
        """Get all data models"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(select(DataModel))
            data_models = result.scalars().all()
            return [DataModelData.model_validate(dm) for dm in data_models]

    async def delete_data_model(self, data_model_id: str) -> DataModelData:
        """Delete a data model by ID"""
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
            data_model_data = DataModelData.model_validate(data_model_obj)
            # Delete associated template file if exists
            if data_model_obj.response_template_file_id:
                await self._delete_template_file(data_model_obj.response_template_file_id)
            await session.delete(data_model_obj)
            await session.commit()
            return data_model_data

    async def update_data_model(
        self, data_model_id: str, data_model_payload: DataModelUpdatePayload, response_template_file: Optional[UploadFile] = None
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

            if response_template_file:
                if data_model_obj.response_template_file_id:
                    await self._delete_template_file(data_model_obj.response_template_file_id)
                data_model_obj.response_template_file_id = await self._upload_template_file(response_template_file)
            if data_model_payload.data_model_mnemonic is not None:
                data_model_obj.data_model_mnemonic = data_model_payload.data_model_mnemonic
            if data_model_payload.pattern_for_data_model is not None:
                data_model_obj.pattern_for_data_model = data_model_payload.pattern_for_data_model

            await session.commit()
            await session.refresh(data_model_obj)
            return DataModelData.model_validate(data_model_obj)

    async def change_response_template_file(
        self, data_model_id: str, response_template_file: Optional[UploadFile] = None
    ) -> DataModelData:
        """Change the response template file for a data model"""
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

            # Delete old template file if exists
            if data_model_obj.response_template_file_id:
                await self._delete_template_file(data_model_obj.response_template_file_id)

            # Upload new template file if provided
            if response_template_file:
                data_model_obj.response_template_file_id = await self._upload_template_file(response_template_file)
            else:
                data_model_obj.response_template_file_id = None

            await session.commit()
            await session.refresh(data_model_obj)
            return DataModelData.model_validate(data_model_obj)

    async def change_active_status(
        self, data_model_id: str, is_active: bool
    ) -> DataModelData:
        """Change the active status of a data model"""
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

            data_model_obj.is_active = is_active

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


    async def _upload_template_file(self, template_file: UploadFile, template_file_id: Optional[str] = None) -> str:
        g2p_template_service = G2PTemplateService.get_component()
        return await g2p_template_service.upload_template_file(template_file, template_file_id)
    
    async def _delete_template_file(self, template_file_id: str) -> None:
        g2p_template_service = G2PTemplateService.get_component()
        return await g2p_template_service.delete_template_file(template_file_id)