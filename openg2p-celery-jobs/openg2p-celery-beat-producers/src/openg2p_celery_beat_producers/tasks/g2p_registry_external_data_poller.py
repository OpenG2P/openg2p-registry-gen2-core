import logging
from typing import List

from openg2p_celery_job_models.models import G2PRegistryExternalDataProvider
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app
from ..config import Settings
from ..engine import Engine
from ..utils import Workers

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = Engine.get_engine()


@celery_app.task(name="g2p_registry_external_data_poller_beat_producer")
def g2p_registry_external_data_poller_beat_producer():
    _logger.info("Processing g2p_registry_external_data_poller_beat_producer")

    session_maker = sessionmaker(bind=_engine, expire_on_commit=False)
    
    with session_maker() as session:
        g2p_registry_external_data_providers: List[G2PRegistryExternalDataProvider] = (
            session.execute(
                select(G2PRegistryExternalDataProvider)
                .filter(
                    G2PRegistryExternalDataProvider.is_active
                    == True
                )
            )
            .scalars()
            .all()
        )
        _logger.info(f"Found {len(g2p_registry_external_data_providers)} active g2p_registry_external_data_providers requests")

        for g2p_registry_external_data_provider in g2p_registry_external_data_providers:
            _logger.info(f"Queueing job from provider_id: {g2p_registry_external_data_provider.provider_id} for processing")

            # Send task to appropriate celery worker
            celery_app.send_task(
                Workers.EXTERNAL_DATA_POLLER,
                args=(g2p_registry_external_data_provider.provider_id,),
                queue=_config.worker_queue,
            )
            _logger.info(
                f"Sent task to {Workers.EXTERNAL_DATA_POLLER} for job from provider_id: {g2p_registry_external_data_provider.provider_id}"
            )
        session.commit()

    _logger.info("Completed processing active g2p_registry_external_data_providers requests")


