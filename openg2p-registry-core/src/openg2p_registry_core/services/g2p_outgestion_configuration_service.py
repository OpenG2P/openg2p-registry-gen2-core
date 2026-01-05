import logging
import uuid
from datetime import datetime
import httpx

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select

from ..models import (
    ProcessStatusEnum,
    OutgoingTopic,
)
from ..schemas import (
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
        

