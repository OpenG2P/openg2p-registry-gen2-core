import json
import logging
from typing import List

from openg2p_registry_core.services import G2PRegisterService
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from openg2p_registry_core.models import (
    ProcessStatusEnum, 
    IncomingClassifiedData, 
    IncomingEnrichedTransformedData
)

from ..app import celery_app
from ..config import Settings
from ..engine import Engine

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = Engine.get_engine()


@celery_app.task(name="data_ingestion_worker")
def data_ingestion_worker(ingest_id: str):
    _logger.info(f"Starting data_ingestion_worker for ingest_id: {ingest_id}")
    session_maker = sessionmaker(
        bind=_engine, expire_on_commit=False
    )

    with session_maker() as session:
        incoming_classified_data: IncomingClassifiedData = None
        try:
            incoming_classified_data = session.get(IncomingClassifiedData, ingest_id)
            incoming_enriched_transformed_data = session.get(IncomingEnrichedTransformedData, ingest_id)
            
            # Logic to ingest data using register services
            # g2p_register_service = G2PRegisterService().get_component()
            

            # Update incoming_classified_data ingestion_status -> PROCESSED
            incoming_classified_data.ingestion_status = ProcessStatusEnum.PROCESSED.value
            incoming_classified_data.ingestion_date_time = func.now()
            session.commit()

        except Exception as e:
            _logger.error(
                f"Error during processing data_ingestion_worker for ingest_id {ingest_id}: {str(e)}"
            )
            # Rollback all sessions
            session.rollback()

            # Update incoming_classified_data ingestion_status -> FAILED
            incoming_classified_data.ingestion_status = ProcessStatusEnum.FAILED.value
            incoming_classified_data.ingestion_date_time = func.now()
            session.commit()
            # Raise exception for testing
            raise e

        _logger.info(
            f"Completed processing data_ingestion_worker for ingest_id: {ingest_id}"
        )