import logging
import importlib
from typing import List

from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker
from openg2p_registry_core.models import (
    G2PRegisterChangeLog,
    G2PRegisterChangeLogPayload,
    G2PRegisterDefinition,
    DeduplicationStatusEnum,
    DeduplicationRegisterResult,
    DeduplicationChangelogResult
)
from openg2p_registry_core.services import G2PRegisterDomainService
from openg2p_registry_core.controller_services import G2PRegisterControllerService

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
            
            # Compute dedup scores
            results = domain_service.compute_deduplication_score(
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


@celery_app.task(name="deduplication_changelog_worker", bind=True, max_retries=3)
def deduplication_changelog_worker(self, change_log_id: str):
    """
    Worker that performs deduplication check against pending changelog records.
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
            
            # Find other pending changelogs for the same register
            other_changelogs = (
                session.execute(
                    select(G2PRegisterChangeLog).where(
                        (G2PRegisterChangeLog.register_id == change_log.register_id) &
                        (G2PRegisterChangeLog.change_log_id != change_log_id)
                    )
                )
            ).scalars().all()
            
            # Compare against each other changelog
            for other_changelog in other_changelogs:
                other_payload = session.get(G2PRegisterChangeLogPayload, other_changelog.change_log_id)
                if not other_payload:
                    continue
                
                score = domain_service._compute_score(
                    change_log_payload.change_payload,
                    type('obj', (object,), other_payload.change_payload)(),
                    register_definition
                )
                
                if score >= (register_definition.dedup_threshold_score or 0):
                    dedup_result = DeduplicationChangelogResult(
                        change_log_id=change_log_id,
                        candidate_change_log_id=other_changelog.change_log_id,
                        match_score=score,
                        field_matches={}
                    )
                    session.add(dedup_result)
            
            # Update status to COMPLETED
            change_log.deduplication_changelog_status = DeduplicationStatusEnum.COMPLETED.value
            change_log.deduplication_changelog_failure_reason = None
            session.commit()
            
            _logger.info(f"Completed deduplication_changelog for change_log: {change_log_id}")
            
        except Exception as e:
            _logger.error(f"Error in deduplication_changelog_worker for change_log {change_log_id}: {str(e)}")
            session.rollback()
            
            if change_log:
                # Retry logic with max_retries
                if self.request.retries < self.max_retries:
                    change_log.deduplication_changelog_status = DeduplicationStatusEnum.PENDING.value
                    _logger.info(f"Retrying deduplication_changelog for change_log: {change_log_id}")
                else:
                    change_log.deduplication_changelog_status = DeduplicationStatusEnum.FAILED.value
                    change_log.deduplication_changelog_failure_reason = str(e)
                    _logger.error(f"Max retries exceeded for change_log: {change_log_id}")
                
                session.add(change_log)
                session.commit()
            
            raise e

