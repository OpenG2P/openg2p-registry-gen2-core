import logging
from typing import List

from openg2p_registry_example_models.models import G2PRegistryExternalDataPayload, StatusEnum
from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker

from ..app import celery_app
from ..config import Settings
from ..engine import Engine
from ..utils import Workers

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = Engine.get_engine()


@celery_app.task(name="g2p_registry_external_data_ingester_beat_producer")
def g2p_registry_external_data_ingester_beat_producer():
    _logger.info("Processing g2p_registry_external_data_ingester_beat_producer")

    session_maker = sessionmaker(bind=_engine, expire_on_commit=False)
    
    with session_maker() as session:
        g2p_registry_external_data_payloads: List[G2PRegistryExternalDataPayload] = (
            session.execute(
                select(G2PRegistryExternalDataPayload)
                .filter(
                    G2PRegistryExternalDataPayload.process_status == StatusEnum.PENDING.value
                )
                .limit(_config.no_of_tasks_to_process)
            )
            .scalars()
            .all()
        )
        _logger.info(f"Found {len(g2p_registry_external_data_payloads)} active g2p_registry_external_data_payload requests")

        for g2p_registry_external_data_payload in g2p_registry_external_data_payloads:
            _logger.info(f"Queueing g2p_registry_external_data_payload with payload_id: {g2p_registry_external_data_payload.payload_id} for processing")

            g2p_registry_external_data_payload.process_status = StatusEnum.PROCESSING.value
            # Send task to appropriate celery worker
            celery_app.send_task(
                Workers.EXTERNAL_DATA_INGESTER,
                args=(g2p_registry_external_data_payload.payload_id,),
                queue=_config.worker_queue,
            )
            _logger.info(
                f"Sent task to {Workers.EXTERNAL_DATA_INGESTER} for ingestion with payload_id: {g2p_registry_external_data_payload.payload_id}"
            )
        session.commit()

    _logger.info("Completed processing pending g2p_registry_external_data_payload requests")
