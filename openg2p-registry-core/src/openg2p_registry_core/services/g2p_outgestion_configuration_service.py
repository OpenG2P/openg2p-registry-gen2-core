import logging
import uuid
from datetime import datetime
from typing import Optional
import httpx

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select, func

from ..models import (
    DataModel,
    G2PRegisterDefinition,
    ProcessStatusEnum,
    OutgoingTemplate,
    OutgoingTopic,
)
from ..schemas import (
    OutgoingTemplateData,
    OutgoingTemplatePayload,
    OutgoingTemplateUpdatePayload,
    OutgoingTopicPayload,
    OutgoingTopicUpdatePayload,
    OutgoingTopicData,
)
from ..errors import G2PRegistryErrorCodes, G2PRegistryException
from ..helpers import WebsubHelper

_logger = logging.getLogger("g2p-outgestion-configuration-service")

class G2POutgestionConfigurationService(BaseService):

    async def create_outgoing_topic(
        self, outgoing_topic_payload: OutgoingTopicPayload
    ) -> list[OutgoingTopicData]:
        """Create a new outgoing topic"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Check if outgoing topic already exists
            await self._check_topic_exists(outgoing_topic_payload, session)
            
            topic_id = outgoing_topic_payload.topic_id or str(uuid.uuid4())

            outgoing_topic = OutgoingTopic(
                topic_id=topic_id,
                register_id=outgoing_topic_payload.register_id,
                data_model_id=outgoing_topic_payload.data_model_id,
                websub_topic=outgoing_topic_payload.websub_topic,
                description=outgoing_topic_payload.description,
            )
            session.add(outgoing_topic)

            await session.commit()
            await session.refresh(outgoing_topic)
            return [OutgoingTopicData.model_validate(outgoing_topic)]

    async def get_outgoing_topic(self, topic_id: str) -> list[OutgoingTopicData]:
        """Get outgoing topic by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            topic_obj = await self._get_outgoing_topic(topic_id, session)
            return [OutgoingTopicData.model_validate(topic_obj)]

    async def get_all_outgoing_topics(self) -> list[OutgoingTopicData]:
        """Get all outgoing topics"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                select(OutgoingTopic).order_by(OutgoingTopic.topic_id)
            )
            topics = result.scalars().all()
            return [OutgoingTopicData.model_validate(topic) for topic in topics]

    async def update_outgoing_topic(
        self, outgoing_topic_payload: OutgoingTopicUpdatePayload
    ) -> list[OutgoingTopicData]:
        """Update outgoing topic - only updates provided fields"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            topic_obj = await self._get_outgoing_topic(outgoing_topic_payload.topic_id, session)

            # Only update fields that are provided (not None)
            if outgoing_topic_payload.register_id is not None:
                topic_obj.register_id = outgoing_topic_payload.register_id
            if outgoing_topic_payload.data_model_id is not None:
                topic_obj.data_model_id = outgoing_topic_payload.data_model_id
            if outgoing_topic_payload.description is not None:
                topic_obj.description = outgoing_topic_payload.description

            await session.commit()
            await session.refresh(topic_obj)
            return [OutgoingTopicData.model_validate(topic_obj)]
    
    async def toggle_outgoing_topic_status(
        self, topic_id: str
    ) -> list[OutgoingTopicData]:
        """Toggle outgoing topic status"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            topic_obj = await self._get_outgoing_topic(topic_id, session)

            topic_obj.is_active = not topic_obj.is_active
            topic_obj.websub_register_status = ProcessStatusEnum.PENDING.value
            topic_obj.websub_register_number_of_attempts = 0
            topic_obj.updated_at = datetime.now()

            await session.commit()
            await session.refresh(topic_obj)
            return [OutgoingTopicData.model_validate(topic_obj)]

    async def re_register_outgoing_topic(
        self, topic_id: str
    ) -> list[OutgoingTopicData]:
        """Re-register outgoing topic"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            topic_obj = await self._get_outgoing_topic(topic_id, session)

            topic_obj.websub_register_status = ProcessStatusEnum.PENDING.value
            topic_obj.websub_register_number_of_attempts = 0
            topic_obj.updated_at = datetime.now()

            await session.commit()
            await session.refresh(topic_obj)
            return [OutgoingTopicData.model_validate(topic_obj)]
    
    async def delete_outgoing_topic(
        self, topic_id: str
    ) -> list[OutgoingTopicData]:
        """Delete outgoing topic"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            topic_obj = await self._get_outgoing_topic(topic_id, session)
            if(topic_obj.is_active):
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.TOPIC_NOT_INACTIVE.value[1],
                    message=G2PRegistryErrorCodes.TOPIC_NOT_INACTIVE.value[0],
                )
            await session.delete(topic_obj)
            await session.commit()
            return [OutgoingTopicData.model_validate(topic_obj)]

    async def create_template(
        self, template_payload: OutgoingTemplatePayload
    ) -> OutgoingTemplateData:
        """Create a new outgoing template"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            await self._validate_register_id_exists(session, template_payload.register_id)
            await self._validate_data_model_id_exists(session, template_payload.data_model_id)
            await self._check_outgoing_template_exists(session, template_payload)

            template = OutgoingTemplate(
                register_id=template_payload.register_id,
                data_model_id=template_payload.data_model_id,
                template_file_id=template_payload.template_file_id,
            )
            session.add(template)
            await session.commit()
            await session.refresh(template)
            return await self._build_template_data_with_mnemonics(session, template)

    async def get_template(self, template_id: str) -> OutgoingTemplateData:
        """Get outgoing template by ID"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template_obj = await self._get_outgoing_template(session, template_id)
            return await self._build_template_data_with_mnemonics(session, template_obj)

    async def get_all_templates(
        self, current_page: int, page_size: int
    ) -> tuple[list[OutgoingTemplateData], int, int]:
        """Get paginated outgoing templates."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            offset = (current_page - 1) * page_size
            total_items_result = await session.execute(
                select(func.count()).select_from(OutgoingTemplate)
            )
            total_items = total_items_result.scalar_one() or 0

            result = await session.execute(
                select(OutgoingTemplate)
                .order_by(OutgoingTemplate.template_id)
                .offset(offset)
                .limit(page_size)
            )
            templates = result.scalars().all()

            template_data_list: list[OutgoingTemplateData] = []
            for template in templates:
                template_data_list.append(
                    await self._build_template_data_with_mnemonics(session, template)
                )

            number_of_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
            return template_data_list, total_items, number_of_pages

    async def update_template(
        self, template_update_payload: OutgoingTemplateUpdatePayload
    ) -> OutgoingTemplateData:
        """Update outgoing template"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template_obj = await self._get_outgoing_template(
                session, template_update_payload.template_id
            )

            if template_update_payload.template_file_id is not None:
                template_obj.template_file_id = template_update_payload.template_file_id

            await session.commit()
            await session.refresh(template_obj)
            return await self._build_template_data_with_mnemonics(session, template_obj)

    async def delete_template(self, template_id: str) -> OutgoingTemplateData:
        """Delete outgoing template by ID and return deleted data."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template_obj = await self._get_outgoing_template(session, template_id)
            deleted_template_data = await self._build_template_data_with_mnemonics(
                session, template_obj
            )
            await session.delete(template_obj)
            await session.commit()
            return deleted_template_data
    

    async def _check_topic_exists(self, outgoing_topic_payload: OutgoingTopicPayload, session: AsyncSession) -> bool:
        if not outgoing_topic_payload.register_id or not outgoing_topic_payload.data_model_id or not outgoing_topic_payload.websub_topic:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.INVALID_REQUEST.value[1],
                message=G2PRegistryErrorCodes.INVALID_REQUEST.value[0],
            )
        existing = await session.execute(
            select(OutgoingTopic).where(
                OutgoingTopic.register_id == outgoing_topic_payload.register_id,
                OutgoingTopic.data_model_id == outgoing_topic_payload.data_model_id,
            )
        )
        if existing.scalar_one_or_none():
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.TOPIC_ALREADY_EXISTS.value[1],
                message=G2PRegistryErrorCodes.TOPIC_ALREADY_EXISTS.value[0],
            )

    async def _check_outgoing_template_exists(
        self, session: AsyncSession, template_payload: OutgoingTemplatePayload
    ) -> None:
        existing_template = await session.execute(
            select(OutgoingTemplate).where(
                OutgoingTemplate.data_model_id == template_payload.data_model_id,
                OutgoingTemplate.register_id == template_payload.register_id,
            )
        )
        if existing_template.scalar_one_or_none():
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.TEMPLATE_ALREADY_EXISTS.value[1],
                message=G2PRegistryErrorCodes.TEMPLATE_ALREADY_EXISTS.value[0],
            )

    async def _get_outgoing_template(
        self, session: AsyncSession, template_id: str
    ) -> OutgoingTemplate:
        if not template_id:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.INVALID_REQUEST.value[1],
                message=G2PRegistryErrorCodes.INVALID_REQUEST.value[0],
            )

        template = await session.execute(
            select(OutgoingTemplate).where(OutgoingTemplate.template_id == template_id)
        )
        template_obj = template.scalar_one_or_none()
        if not template_obj:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.TEMPLATE_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.TEMPLATE_NOT_FOUND.value[0],
            )
        return template_obj

    async def _validate_data_model_id_exists(
        self, session: AsyncSession, data_model_id: str
    ) -> DataModel:
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
        existing = await session.execute(
            select(G2PRegisterDefinition).where(
                G2PRegisterDefinition.register_id == register_id
            )
        )
        existing = existing.scalar_one_or_none()
        if not existing:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0],
            )
        return existing

    async def _build_template_data_with_mnemonics(
        self, session: AsyncSession, template_obj: OutgoingTemplate
    ) -> OutgoingTemplateData:
        register_obj = await self._validate_register_id_exists(session, template_obj.register_id)
        data_model_obj = await self._validate_data_model_id_exists(
            session, template_obj.data_model_id
        )

        return OutgoingTemplateData(
            template_id=template_obj.template_id,
            register_id=template_obj.register_id,
            register_mnemonic=register_obj.register_mnemonic,
            data_model_id=template_obj.data_model_id,
            data_model_mnemonic=data_model_obj.data_model_mnemonic,
            template_file_id=template_obj.template_file_id,
        )

    async def _get_outgoing_topic(self, topic_id: str, session: AsyncSession) -> OutgoingTopic:
        if topic_id is None:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.INVALID_REQUEST.value[1],
                message=G2PRegistryErrorCodes.INVALID_REQUEST.value[0],
            )
        topic = await session.execute(
            select(OutgoingTopic).where(OutgoingTopic.topic_id == topic_id)
        )
        topic_obj = topic.scalar_one_or_none()
        if not topic_obj:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.TOPIC_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.TOPIC_NOT_FOUND.value[0],
            )
        return topic_obj
        

