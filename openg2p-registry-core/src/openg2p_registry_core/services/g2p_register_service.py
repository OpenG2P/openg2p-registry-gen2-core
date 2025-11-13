import logging
import uuid
import importlib

from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from openg2p_registry_core.schemas.payload import ChangeLogPayload
from sqlalchemy.orm import Session
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models import G2PRegisterChangeLog, G2PRegisterDefinition, G2PRegisterOperation, G2PRegisterVerification, ApprovalStatusEnum
from ..schemas import ChangeLogRequest
from ..errors import G2PRegistryErrorCodes, G2PRegistryException

_logger = logging.getLogger('g2p-register-service')
_engine = dbengine.get()

class G2PRegisterService(BaseService):

    async def create_change_log(self, change_log_request: ChangeLogRequest):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            
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

    async def get_change_logs(self, internal_record_id: str):
        pass

    async def get_change_log(self, change_log_id: str):
        pass

    async def approve_change_log(self, change_log_id: str):
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            # Validate change log exists and is pending approval
            change_log = await self.validate_change_log_exists(change_log_id, session)
            _logger.info(f"Validated change log for approval: {change_log}")
            await self.validate_change_log_operation(change_log, session)
            # Validate whether verifications are done
            await self.validate_change_log_verifications(change_log, session)
            # Ensure there are no earlier change logs for the internal_record_id pending approval
            await self.validate_change_log_sequence(change_log, session)
            # In case of approval, insert data into register_history 
            await self.insert_into_register_history(change_log, session)
            # Upsert data into register
            await self.insert_into_register(change_log, session)
            # Mark change log as approved
            change_log.approval_status = ApprovalStatusEnum.APPROVED.value
            change_log.approved_by = "system"
            change_log.approved_at = func.now()
            await session.commit()
            await session.refresh(change_log)
            return change_log

    async def validate_change_log_operation(self, g2p_register_change_log: G2PRegisterChangeLog, session) -> None:
        g2p_register_operation: G2PRegisterOperation = (
            await session.execute(
                select(G2PRegisterOperation).where(
                    G2PRegisterOperation.operation_id == g2p_register_change_log.operation_id
                )
            )
        ).scalar()
        if not g2p_register_operation:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.OPERATION_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.OPERATION_NOT_FOUND.value[0]
            )
        if g2p_register_operation.is_new_operation:
            # create and assign a new internal_record_id
            internal_record_id = str(uuid.uuid4())
            g2p_register_change_log.internal_record_id = internal_record_id
        


        
    async def validate_change_log_exists(self, change_log_id: str, session) -> G2PRegisterChangeLog:
        _logger.info(f"Validating change log exists for ID: {change_log_id}")
        change_log: G2PRegisterChangeLog = (
            await session.execute(
                select(G2PRegisterChangeLog).where(
                    G2PRegisterChangeLog.change_log_id == change_log_id
                )
            )
        ).scalar()
        if not change_log:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.CHANGE_LOG_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.CHANGE_LOG_NOT_FOUND.value[0]
            )
        if change_log.approval_status != ApprovalStatusEnum.PENDING.value:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.CHANGE_LOG_NOT_IN_PENDING_STATE.value[1],
                message=G2PRegistryErrorCodes.CHANGE_LOG_NOT_IN_PENDING_STATE.value[0]
            )
        return change_log

    async def validate_change_log_verifications(self, change_log: G2PRegisterChangeLog, session) -> None:
        verifications_count = (
            await session.execute(
                select(func.count()).select_from(G2PRegisterVerification).where(
                    G2PRegisterVerification.change_log_id == change_log.change_log_id
                )
            )
        ).scalar_one() # TODO: Check if we need to call this or check no_of_verifications_done field
        if verifications_count < (change_log.no_of_verifications_required or 0):
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.VERIFICATIONS_PENDING.value[1],
                message=G2PRegistryErrorCodes.VERIFICATIONS_PENDING.value[0]
            )

    async def validate_change_log_sequence(self, change_log: G2PRegisterChangeLog, session) -> None:
        earlier_pending = (
            await session.execute(
                select(G2PRegisterChangeLog).where(
                    G2PRegisterChangeLog.internal_record_id == change_log.internal_record_id,
                    G2PRegisterChangeLog.approval_status == "PENDING",
                    G2PRegisterChangeLog.created_at < change_log.created_at,
                )
            )
        ).scalars().first()
        if earlier_pending:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1],
                message="There are earlier pending change logs for this record"
            )

    async def insert_into_register_history(self, change_log: G2PRegisterChangeLog, session) -> None:
        # Resolve history model class dynamically based on register mnemonic
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == change_log.register_id
                )
            )
        ).scalar()
        if not register_definition:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[1],
                message=G2PRegistryErrorCodes.REGISTER_NOT_FOUND.value[0]
            )
        module = importlib.import_module("openg2p_registry_extensions.models")
        history_class_prefix = "G2PRegisterHistory"
        implementation_class_name = f"{history_class_prefix}{register_definition.register_mnemonic}"
        history_class = getattr(module, implementation_class_name)

        schema_module = importlib.import_module("openg2p_registry_extensions.schemas")
        schema_class_prefix = "G2PRegisterHistorySchema"
        schema_class_name = f"{schema_class_prefix}{register_definition.register_mnemonic}"
        history_schema_class = getattr(schema_module, schema_class_name)

        # Serialize change log payload to history schema
        history_schema_instance = history_schema_class(**(change_log.change_payload or {}))

        history_schema_instance.history_record_id = str(uuid.uuid4())
        history_schema_instance.internal_record_id = change_log.internal_record_id
        history_schema_instance.change_log_id = change_log.change_log_id
        history_schema_instance.created_at = func.now()
        history_schema_instance.created_by = "system" # TODO: Replace with actual user info
        history_schema_instance.approved_at = func.now()
        history_schema_instance.approved_by = "system" # TODO: Replace with actual user info
        history_instance = history_class(
            **history_schema_instance.dict()
        )

        session.add(history_instance)

    async def insert_into_register(self, change_log: G2PRegisterChangeLog, session) -> None:
        # Resolve register model class dynamically based on register mnemonic
        register_definition: G2PRegisterDefinition = (
            await session.execute(
                select(G2PRegisterDefinition).where(
                    G2PRegisterDefinition.register_id == change_log.register_id
                )
            )
        ).scalar()
        module = importlib.import_module("openg2p_registry_extensions.models")
        register_class_prefix = "G2PRegister"
        implementation_class_name = f"{register_class_prefix}{register_definition.register_mnemonic}"
        register_class = getattr(module, implementation_class_name)

        existing = (
            await session.execute(
                select(register_class).where(
                    register_class.internal_record_id == change_log.internal_record_id
                )
            )
        ).scalar()

        schema_module = importlib.import_module("openg2p_registry_extensions.schemas")
        schema_class_prefix = "G2PRegisterSchema"
        schema_class_name = f"{schema_class_prefix}{register_definition.register_mnemonic}"
        schema_class = getattr(schema_module, schema_class_name)

        # Serialize change log payload to register schema
        register_schema_instance = schema_class(**(change_log.change_payload or {}))
        if existing:
            for key, value in register_schema_instance.dict().items():
                setattr(existing, key, value)
            setattr(existing, "last_approved_at", func.now())
            setattr(existing, "last_approved_by", "system")
            new_instance = existing
        else:
            register_schema_instance.internal_record_id = change_log.internal_record_id
            register_schema_instance.created_at = func.now()
            register_schema_instance.created_by = "system" # TODO: Replace with actual user info
            register_schema_instance.last_approved_at = func.now()
            register_schema_instance.last_approved_by = "system"
            new_instance = register_class(**register_schema_instance.dict())

        # payload = dict(change_log.change_payload or {})
        # if existing:
        #     for key, value in payload.items():
        #         setattr(existing, key, value)
        #     setattr(existing, "last_approved_at", func.now())
        #     setattr(existing, "last_approved_by", "system")
        # else:
        #     payload["internal_record_id"] = change_log.internal_record_id
        #     payload["created_at"] = func.now()
        #     payload["created_by"] = "system" # TODO: Replace with actual user info
        #     payload["last_approved_at"] = func.now()
        #     payload["last_approved_by"] = "system"
        #     new_instance = register_class(**payload)
            session.add(new_instance)
        

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
