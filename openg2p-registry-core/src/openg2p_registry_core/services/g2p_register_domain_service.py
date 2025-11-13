import logging
import uuid
import importlib

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from openg2p_registry_core.schemas.payload import ChangeLogPayload
from sqlalchemy.orm import Session
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models import G2PRegisterChangeLog, G2PRegisterDefinition, G2PRegisterOperation, G2PRegisterVerification
from ..schemas import ChangeLogRequest
from ..errors import G2PRegistryErrorCodes, G2PRegistryException

_logger = logging.getLogger('g2p-register-domain-service')
_engine = dbengine.get()

class G2PRegisterDomainService(BaseService):

    async def validate_domain_attributes(self, change_log_payload: ChangeLogPayload):
        pass