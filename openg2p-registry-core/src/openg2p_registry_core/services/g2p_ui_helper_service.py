import logging
import uuid
from typing import List

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select

from ..models import (
    G2PInputMechanism
)
from ..schemas import (
    G2PInputMechanismData,
)
from ..errors import G2PRegistryErrorCodes, G2PRegistryException

_logger = logging.getLogger("g2p-ui-helper-service")

class G2PUIHelperService(BaseService):

    async def get_all_input_mechanisms(self) -> List[G2PInputMechanismData]:
        """Get all registry input mechanisms"""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            g2p_input_mechanisms = (
                await session.execute(
                    select(G2PInputMechanism)
                )
            ).scalars().all()

            _logger.info(f"Got {len(g2p_input_mechanisms)} input mechanisms")

            input_mechanism_data: List[G2PInputMechanismData] = []
            for g2p_input_mechanism in g2p_input_mechanisms:
                input_mechanism_data.append(G2PInputMechanismData.model_validate(g2p_input_mechanism))

            return input_mechanism_data
