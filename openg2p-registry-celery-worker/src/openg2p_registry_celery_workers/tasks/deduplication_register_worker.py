import logging
import importlib

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from openg2p_registry_core.models import (
    G2PRegisterChangeLog,
    G2PRegisterChangeLogPayload,
    G2PRegisterDefinition,
    DeduplicationStatusEnum,
    DeduplicationRegisterResult,
)


from ..app import celery_app
from ..config import Settings
from ..engine import Engine

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = Engine.get_engine()


@celery_app.task(name="deduplication_register_worker", bind=True, max_retries=3)
def deduplication_register_worker(self, change_log_id: str):
    """
    Worker that performs deduplication check against register records.
    Retries up to 3 times on failure.
    """
    session_maker = sessionmaker(bind=_engine, expire_on_commit=False)
    
    with session_maker() as session:
        change_log: G2PRegisterChangeLog = None
        try:
            # Fetch change log and payload
            change_log = session.get(G2PRegisterChangeLog, change_log_id)
            if not change_log:
                raise Exception(f"Change log not found: {change_log_id}")
            
            change_log_payload = session.get(G2PRegisterChangeLogPayload, change_log_id)
            if not change_log_payload:
                raise Exception(f"Change log payload not found: {change_log_id}")
            
            # Get domain service
            domain_factory_module = importlib.import_module(
                "openg2p_registry_extensions.register_domain.factory"
            )
            domain_factory = getattr(domain_factory_module, "G2PRegisterDomainFactory").get_component()
            
            register_definition = session.get(G2PRegisterDefinition, change_log.register_id)
            domain_service = domain_factory.get_domain_service(register_definition.register_mnemonic)

            # Compute dedup scores using public service method
            results = domain_service.compute_deduplication_score_for_register(
                change_log_id,
                change_log.register_id,
                change_log_payload.change_payload,
                session
            )

            # Save results
            for result in results:
                dedup_result = DeduplicationRegisterResult(
                    change_log_id=change_log_id,
                    internal_record_id=result["candidate_id"],
                    match_score=result["score"],
                    field_matches=result.get("field_matches", {})
                )
                session.add(dedup_result)
            
            # Update status to COMPLETED
            change_log.deduplication_register_status = DeduplicationStatusEnum.COMPLETED.value
            change_log.deduplication_register_failure_reason = None
            session.commit()
            
            _logger.info(f"Completed deduplication_register for change_log: {change_log_id}")
            
        except Exception as e:
            _logger.error(f"Error in deduplication_register_worker for change_log {change_log_id}: {str(e)}")
            session.rollback()
            
            if change_log:
                # Retry logic with max_retries
                if self.request.retries < self.max_retries:
                    change_log.deduplication_register_status = DeduplicationStatusEnum.PENDING.value
                    _logger.info(f"Retrying deduplication_register for change_log: {change_log_id}")
                else:
                    change_log.deduplication_register_status = DeduplicationStatusEnum.FAILED.value
                    change_log.deduplication_register_failure_reason = str(e)
                    _logger.error(f"Max retries exceeded for change_log: {change_log_id}")
                
                session.add(change_log)
                session.commit()
            
            raise e

