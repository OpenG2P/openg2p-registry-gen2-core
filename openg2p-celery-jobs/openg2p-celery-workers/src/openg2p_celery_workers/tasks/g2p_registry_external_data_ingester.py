import logging
import requests
from requests import Response
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from openg2p_registry_example_models.models import (
    StatusEnum, 
    G2PRegistryExternalDataProvider,
    G2PRegistryExternalDataPayload,
)
from openg2p_registry_core.schemas import IngestDataResponse

from ..app import celery_app
from ..config import Settings
from ..engine import Engine
from ..utils import HelperFactory, HelperInterface

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = Engine.get_engine()


@celery_app.task(name="g2p_registry_external_data_ingester_worker")
def g2p_registry_external_data_ingester_worker(payload_id: str):
    _logger.info(f"Processing g2p_registry_external_data_ingester_worker")
    session_maker = sessionmaker(
        bind=_engine, expire_on_commit=False
    )

    with session_maker() as session:
        g2p_registry_external_data_payload: G2PRegistryExternalDataPayload | None = None
        
        try:
            g2p_registry_external_data_payload = session.get(G2PRegistryExternalDataPayload, payload_id)
            g2p_registry_external_data_provider = session.get(G2PRegistryExternalDataProvider, g2p_registry_external_data_payload.provider_id)

            ingest_helper: HelperInterface = HelperFactory.get_helper(g2p_registry_external_data_provider.helper_code)

            ingest_response: IngestDataResponse = ingest_helper.post_ingest_request(
                data_model=g2p_registry_external_data_provider.data_model,
                request_body=g2p_registry_external_data_payload.payload_json,
                request_headers=g2p_registry_external_data_payload.payload_headers
            )

            if ingest_response.status_code == 200:
                _logger.info(
                    f"Registry ingestion request successful for payload_id {payload_id} successful with status code: {ingest_response.status_code}"
                )
                
                g2p_registry_external_data_payload.registry_ingest_id = ingest_response.response_body.response_payload.ingest_id
                g2p_registry_external_data_payload.process_number_of_attempts += 1
                g2p_registry_external_data_payload.process_status = StatusEnum.SUCCESS.value
                g2p_registry_external_data_payload.process_latest_datetime = func.now()

            else:
                raise Exception(f"Ingestion failed for payload_id {payload_id} with status code: {ingest_response.status_code}")           
            
            session.commit()

        except Exception as e:
            _logger.error(
                f"Error during processing g2p_registry_external_data_ingester_worker for payload_id {payload_id}: {str(e)}"
            )
            session.rollback()

            g2p_registry_external_data_payload.process_status = (
                StatusEnum.PENDING.value
                if g2p_registry_external_data_payload.process_number_of_attempts < _config.worker_max_attempts
                else StatusEnum.FAILED.value
            )
            g2p_registry_external_data_payload.process_number_of_attempts += 1
            g2p_registry_external_data_payload.process_latest_error_code = str(e)
            g2p_registry_external_data_payload.process_latest_datetime = func.now()

            session.commit()
            # Raise exception for testing
            raise e

        _logger.info(
            f"Completed processing g2p_registry_external_data_ingester_worker for payload_id: {payload_id}"
        )
