import logging
import uuid
import importlib

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from openg2p_registry_core.schemas.payload import ChangeLogPayload
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models import G2PRegisterChangeLog, G2PRegisterDefinition, G2PRegisterOperation
from ..schemas import ChangeLogRequest
from ..errors import G2PRegistryErrorCodes, G2PRegistryException

_logger = logging.getLogger('g2p-register-service')
_engine = dbengine.get()

class G2PRegisterService(BaseService):
    pass

    async def create_change_log(self, change_log_request: ChangeLogRequest):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate the change log before creating
            await self.validate_change_log(change_log_request.request_body.request_payload.operation_id)
            
            g2p_register_definition: G2PRegisterDefinition = await self.validate_register_definition(change_log_request.request_body.request_payload.register_id, session)
            g2p_register_operation: G2PRegisterOperation = await self.validate_operation(change_log_request.request_body.request_payload.operation_id, session)

            if not g2p_register_operation.is_new_operation:
                # Check whether the record exists with given internal_record_id
                await self.validate_internal_record(g2p_register_definition, change_log_request.request_body.request_payload.internal_record_id, session)
                    
            g2p_register_change_log: G2PRegisterChangeLog = await self.construct_change_log(change_log_request, g2p_register_operation)
            
            session.add(g2p_register_change_log)
            await session.commit()
            # Refresh to get any DB defaults
            await session.refresh(g2p_register_change_log)

            return g2p_register_change_log

    async def get_change_logs(self):
        pass

    async def validate_change_log(self, change_log_payload: ChangeLogPayload):
        pass

    async def approve_change_log(self, change_log_id: str):
        pass

    async def validate_register_definition(self, register_id: str, session) -> G2PRegisterDefinition:
        g2p_register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == register_id
                )
            )
        ).scalar()
        if not g2p_register_definition:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0]
            )
            
        return g2p_register_definition

    async def validate_operation(self, operation_id: str, session) -> G2PRegisterOperation:

        g2p_register_operation: G2PRegisterOperation =(
                await session.execute(
                select(G2PRegisterOperation).where(
                    G2PRegisterOperation.operation_id == operation_id
                )
            )
        ).scalar()
        if not g2p_register_operation:
            raise ValueError(f"Operation with ID {operation_id} does not exist.")
            
        return g2p_register_operation


    async def validate_internal_record(self, g2p_register_definition: G2PRegisterDefinition, internal_record_id: str, session: Session) -> None:
        
        module = importlib.import_module("openg2p_registry_extensions.models")

        register_class_prefix = "G2PRegister"
        implementation_class_name = f"{register_class_prefix}{g2p_register_definition.register_mnemonic}"

        implementation_class = getattr(module, implementation_class_name)
        _logger.debug(f"Validating internal record for class: {implementation_class}")

        internal_record = (
            await session.execute(
                select(implementation_class).where(
                    implementation_class.internal_record_id == internal_record_id
                )
            )
        ).scalar()
        _logger.debug(f"Internal record fetched: {internal_record}")
        if not internal_record:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.REGISTER_DATA_NOT_FOUND.value[0]
            )

    async def construct_change_log(self, change_log_request: ChangeLogRequest, g2p_register_operation: G2PRegisterOperation) -> G2PRegisterChangeLog:
        change_log_id = str(uuid.uuid4())
        if g2p_register_operation.is_new_operation:
            change_log_request.request_body.request_payload.internal_record_id = str(uuid.uuid4())
        g2p_register_change_log = G2PRegisterChangeLog(
            change_log_id=change_log_id,
            register_id=change_log_request.request_body.request_payload.register_id,
            internal_record_id=change_log_request.request_body.request_payload.internal_record_id,
            operation_id=change_log_request.request_body.request_payload.operation_id,
            change_payload=change_log_request.request_body.request_payload.change_payload,
            source_partner_id=change_log_request.request_header.sender_app_mnemonic,
            created_by="system",  # TODO: Replace with actual user info
            created_at=func.now(),
            no_of_verifications_required=g2p_register_operation.no_of_verifications_required,
            no_of_verifications_done=0,
            approval_status=change_log_request.request_body.request_payload.approval_status.value,
        )    
        return g2p_register_change_log
