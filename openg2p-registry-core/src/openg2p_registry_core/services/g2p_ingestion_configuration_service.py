import logging
import uuid
from typing import Optional, List
import httpx
from fastapi import UploadFile

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select

from ..models import (
    IncomingModelKeyPath,
    IncomingModelSemanticPattern,
    IncomingTemplate,
    DataModel,
    SubscriptionActivityLog,
    G2PRegisterDefinition,
    G2PRegisterSection,
)
from ..schemas import (
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

_logger = logging.getLogger("g2p-ingestion-configuration-service")


class G2PIngestionConfigurationService(BaseService):

    # IncomingModelKeyPath Methods
    async def create_incoming_key_path(
        self, pattern_payload: IncomingModelKeyPathPayload
    ) -> IncomingModelKeyPathData:
        """Create a new incoming key path"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self._check_incoming_key_path_id_exists(
                session, pattern_payload.key_path_id
            )
            await self._validate_data_model_id_exists(
                session, pattern_payload.data_model_id
            )
            await self._check_incoming_key_path_data_model_exists(
                session, pattern_payload.data_model_id
            )
            pattern = IncomingModelKeyPath(
                data_model_id=pattern_payload.data_model_id,
                key_path_for_message_id=pattern_payload.key_path_for_message_id,
                key_path_for_sender=pattern_payload.key_path_for_sender,
                key_path_for_signature=pattern_payload.key_path_for_signature,
                key_path_for_signature_payload=pattern_payload.key_path_for_signature_payload,
                is_list=pattern_payload.is_list,
                key_path_for_list_elements=pattern_payload.key_path_for_list_elements,
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

    async def get_incoming_key_path(self, key_path_id: str) -> IncomingModelKeyPathData:
        """Get incoming key path by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern_obj = await self._get_incoming_key_path(session, key_path_id)
            return IncomingModelKeyPathData.model_validate(pattern_obj)

    async def update_incoming_key_path(
        self, key_path_id: str, pattern_payload: IncomingModelKeyPathUpdatePayload
    ) -> IncomingModelKeyPathData:
        """Update incoming key path - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern_obj = await self._get_incoming_key_path(session, key_path_id)

            if pattern_payload.key_path_for_message_id is not None:
                pattern_obj.key_path_for_message_id = pattern_payload.key_path_for_message_id
            if pattern_payload.key_path_for_sender is not None:
                pattern_obj.key_path_for_sender = pattern_payload.key_path_for_sender
            if pattern_payload.key_path_for_signature is not None:
                pattern_obj.key_path_for_signature = pattern_payload.key_path_for_signature
            if pattern_payload.key_path_for_signature_payload is not None:
                pattern_obj.key_path_for_signature_payload = (
                    pattern_payload.key_path_for_signature_payload
                )
            if pattern_payload.is_list is not None:
                pattern_obj.is_list = pattern_payload.is_list
            if pattern_payload.key_path_for_list_elements is not None:
                pattern_obj.key_path_for_list_elements = (
                    pattern_payload.key_path_for_list_elements
                )

            await session.commit()
            await session.refresh(pattern_obj)
            return IncomingModelKeyPathData.model_validate(pattern_obj)

    async def delete_incoming_key_path(self, key_path_id: str) -> IncomingModelKeyPathData:
        """Delete incoming key path and return deleted data."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern_obj = await self._get_incoming_key_path(session, key_path_id)
            deleted_pattern_data = IncomingModelKeyPathData.model_validate(pattern_obj)
            await session.delete(pattern_obj)
            await session.commit()
            return deleted_pattern_data

    async def _get_incoming_key_path(
        self, session: AsyncSession, key_path_id: str
    ) -> IncomingModelKeyPath:
        """Get incoming key path by ID - helper method"""
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
        return pattern_obj

    async def _check_incoming_key_path_id_exists(
        self, session: AsyncSession, key_path_id: Optional[str]
    ) -> None:
        """Raise an exception when a provided key_path_id already exists."""
        if not key_path_id:
            return

        existing = await session.execute(
            select(IncomingModelKeyPath).where(
                IncomingModelKeyPath.key_path_id == key_path_id
            )
        )
        if existing.scalar_one_or_none():
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.PATTERN_ALREADY_EXISTS.value[1],
                message=G2PRegistryErrorCodes.PATTERN_ALREADY_EXISTS.value[0],
            )

    async def _validate_data_model_id_exists(
        self, session: AsyncSession, data_model_id: str
    ) -> DataModel:
        """Validate and return the data model for a given data_model_id."""
        existing = await session.execute(
            select(DataModel).where(DataModel.data_model_id == data_model_id)
        )
        existing = existing.scalar_one_or_none()
        if not existing:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.DATA_MODEL_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.DATA_MODEL_NOT_FOUND.value[0],
            )
        return existing
    
    async def _validate_register_id_exists(
        self, session: AsyncSession, register_id: str
    ) -> G2PRegisterDefinition:
        """Validate and return the register definition for a given register_id."""
        existing = await session.execute(
            select(G2PRegisterDefinition).where(G2PRegisterDefinition.register_id == register_id)
        )
        existing = existing.scalar_one_or_none()
        if not existing:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0],
            )
        return existing
    
    async def _validate_section_id_exists(
        self, session: AsyncSession, section_id: str
    ) -> G2PRegisterSection:
        """Validate and return the section for a given section_id."""
        existing = await session.execute(
            select(G2PRegisterSection).where(
                G2PRegisterSection.section_id == section_id
            )
        )
        existing = existing.scalar_one_or_none()
        if not existing:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.SECTION_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.SECTION_NOT_FOUND.value[0],
            )
        return existing

    async def _check_incoming_key_path_data_model_exists(
        self, session: AsyncSession, data_model_id: str
    ) -> None:
        """Raise an exception if an IncomingModelKeyPath already exists for the data model."""
        existing = await session.execute(
            select(IncomingModelKeyPath).where(
                IncomingModelKeyPath.data_model_id == data_model_id
            )
        )
        if existing.scalar_one_or_none():
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.PATTERN_ALREADY_EXISTS_FOR_DATA_MODEL.value[1],
                message=G2PRegistryErrorCodes.PATTERN_ALREADY_EXISTS_FOR_DATA_MODEL.value[0],
            )

    # IncomingModelSemanticPattern Methods
    async def create_semantic_pattern(
        self, pattern_payload: IncomingModelSemanticPatternPayload
    ) -> IncomingModelSemanticPatternData:
        """Create a new semantic pattern"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self._validate_data_model_id_exists(session, pattern_payload.data_model_id)
            await self._validate_register_id_exists(session, pattern_payload.register_id)
            await self._validate_section_id_exists(session, pattern_payload.section_id)
            pattern = IncomingModelSemanticPattern(
                data_model_id=pattern_payload.data_model_id,
                register_id=pattern_payload.register_id,
                section_id=pattern_payload.section_id,
                pattern_for_register=pattern_payload.pattern_for_register,
                pattern_for_section=pattern_payload.pattern_for_section,
                key_path_for_business_payload=pattern_payload.key_path_for_business_payload,
                raw_payload_enricher_class=pattern_payload.raw_payload_enricher_class,
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
            pattern_obj = await self._get_semantic_pattern(session, semantic_pattern_id)
            return await self._build_semantic_pattern_data_with_mnemonics(session, pattern_obj)

    async def get_all_semantic_patterns(self) -> list[IncomingModelSemanticPatternData]:
        """Get all semantic patterns"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(select(IncomingModelSemanticPattern))
            patterns = result.scalars().all()
            semantic_patterns: list[IncomingModelSemanticPatternData] = []
            for pattern in patterns:
                semantic_patterns.append(
                    await self._build_semantic_pattern_data_with_mnemonics(session, pattern)
                )
            return semantic_patterns

    async def update_semantic_pattern(
        self, semantic_pattern_id: str, pattern_payload: IncomingModelSemanticPatternUpdatePayload
    ) -> IncomingModelSemanticPatternData:
        """Update semantic pattern - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern_obj = await self._get_semantic_pattern(session, semantic_pattern_id)

            if pattern_payload.pattern_for_register is not None:
                pattern_obj.pattern_for_register = pattern_payload.pattern_for_register
            if pattern_payload.pattern_for_section is not None:
                pattern_obj.pattern_for_section = pattern_payload.pattern_for_section
            if pattern_payload.key_path_for_business_payload is not None:
                pattern_obj.key_path_for_business_payload = pattern_payload.key_path_for_business_payload
            if pattern_payload.raw_payload_enricher_class is not None:
                pattern_obj.raw_payload_enricher_class = pattern_payload.raw_payload_enricher_class

            await session.commit()
            await session.refresh(pattern_obj)
            return IncomingModelSemanticPatternData.model_validate(pattern_obj)

    async def delete_semantic_pattern(self, semantic_pattern_id: str) -> IncomingModelSemanticPatternData:
        """Delete semantic pattern by ID and return deleted data."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            pattern_obj = await self._get_semantic_pattern(session, semantic_pattern_id)
            deleted_pattern_data = await self._build_semantic_pattern_data_with_mnemonics(
                session, pattern_obj
            )
            await session.delete(pattern_obj)
            await session.commit()
            return deleted_pattern_data

    async def _get_semantic_pattern(
        self, session: AsyncSession, semantic_pattern_id: str
    ) -> IncomingModelSemanticPattern:
        """Get semantic pattern by ID - helper method"""
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
        return pattern_obj

    async def _build_semantic_pattern_data_with_mnemonics(
        self, session: AsyncSession, pattern_obj: IncomingModelSemanticPattern
    ) -> IncomingModelSemanticPatternData:
        """Build semantic pattern response with related mnemonics."""
        data_model_obj = await self._validate_data_model_id_exists(
            session, pattern_obj.data_model_id
        )
        register_obj = await self._validate_register_id_exists(
            session, pattern_obj.register_id
        )
        section_obj = await self._validate_section_id_exists(
            session, pattern_obj.section_id
        )

        return IncomingModelSemanticPatternData(
            semantic_pattern_id=pattern_obj.semantic_pattern_id,
            data_model_id=pattern_obj.data_model_id,
            data_model_mnemonic=data_model_obj.data_model_mnemonic,
            register_id=pattern_obj.register_id,
            register_mnemonic=register_obj.register_mnemonic,
            section_id=pattern_obj.section_id,
            section_mnemonic=section_obj.section_mnemonic,
            pattern_for_register=pattern_obj.pattern_for_register,
            pattern_for_section=pattern_obj.pattern_for_section,
            key_path_for_business_payload=pattern_obj.key_path_for_business_payload,
            raw_payload_enricher_class=pattern_obj.raw_payload_enricher_class,
        )

    # IncomingTemplate Methods
    async def create_template(
        self, template_payload: IncomingTemplatePayload
    ) -> IncomingTemplateData:
        """Create a new template"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self._validate_register_id_exists(session, template_payload.register_id)
            await self._validate_data_model_id_exists(session, template_payload.data_model_id)
            await self._check_incoming_template_exists(session, template_payload)

            template: IncomingTemplate = IncomingTemplate(
                register_id=template_payload.register_id,
                data_model_id=template_payload.data_model_id,
                template_file_id=template_payload.template_file_id,
                jsonld_expansion_required=template_payload.jsonld_expansion_required,
            )
            session.add(template)
            await session.commit()
            await session.refresh(template)
            return await self._build_template_data_with_mnemonics(session, template)

    async def get_template(self, template_id: str) -> IncomingTemplateData:
        """Get template by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template_obj: IncomingTemplate = await self._get_incoming_template(session, template_id)
            return await self._build_template_data_with_mnemonics(session, template_obj)

    async def get_all_templates(self) -> list[IncomingTemplateData]:
        """Get all templates"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(select(IncomingTemplate))
            templates = result.scalars().all()

            template_data_list: list[IncomingTemplateData] = []
            for template in templates:
                template_data_list.append(
                    await self._build_template_data_with_mnemonics(session, template)
                )
            return template_data_list

    async def update_template(
        self, template_update_payload: IncomingTemplateUpdatePayload
    ) -> IncomingTemplateData:
        """Update template - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template_obj: IncomingTemplate = await self._get_incoming_template(
                session, template_update_payload.template_id
            )

            if template_update_payload.template_file_id is not None:
                template_obj.template_file_id = template_update_payload.template_file_id
            if template_update_payload.jsonld_expansion_required is not None:
                template_obj.jsonld_expansion_required = (
                    template_update_payload.jsonld_expansion_required
                )

            await session.commit()
            await session.refresh(template_obj)
            return await self._build_template_data_with_mnemonics(session, template_obj)

    async def delete_template(self, template_id: str) -> IncomingTemplateData:
        """Delete template by ID and return deleted data."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template_obj: IncomingTemplate = await self._get_incoming_template(session, template_id)
            deleted_template_data = await self._build_template_data_with_mnemonics(
                session, template_obj
            )
            await session.delete(template_obj)
            await session.commit()
            return deleted_template_data

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
        """Check if template with same data_model_id and register_id already exists."""
        if not template_payload.data_model_id or not template_payload.register_id:
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

    async def _build_template_data_with_mnemonics(
        self, session: AsyncSession, template_obj: IncomingTemplate
    ) -> IncomingTemplateData:
        """Build incoming template response with register and data model mnemonics."""
        register_obj = await self._validate_register_id_exists(session, template_obj.register_id)
        data_model_obj = await self._validate_data_model_id_exists(session, template_obj.data_model_id)

        return IncomingTemplateData(
            template_id=template_obj.template_id,
            register_id=template_obj.register_id,
            register_mnemonic=register_obj.register_mnemonic,
            data_model_id=template_obj.data_model_id,
            data_model_mnemonic=data_model_obj.data_model_mnemonic,
            template_file_id=template_obj.template_file_id,
            jsonld_expansion_required=template_obj.jsonld_expansion_required,
        )

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

    async def get_all_subscription_activity_logs(self) -> list[SubscriptionActivityLogData]:
        """Get all subscription activity logs"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(SubscriptionActivityLog).order_by(
                    SubscriptionActivityLog.date_time.desc()
                )
            )
            activity_logs = result.scalars().all()
            return [SubscriptionActivityLogData.model_validate(log) for log in activity_logs]


    async def _upload_template_file(self, template_file: UploadFile, template_file_id: Optional[str] = None) -> str:
        g2p_template_service = G2PTemplateService.get_component()
        return await g2p_template_service.upload_template_file(template_file, template_file_id)
    
    async def _delete_template_file(self, template_file_id: str) -> None:
        g2p_template_service = G2PTemplateService.get_component()
        return await g2p_template_service.delete_template_file(template_file_id)
