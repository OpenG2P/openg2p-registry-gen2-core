# ruff: noqa: E402

import asyncio
import logging
from datetime import timedelta
from .config import Settings
_config = Settings.get_config()

from celery import Celery
from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.exception import BaseExceptionHandler
from openg2p_celery_job_models.models import G2PRegistryExternalDataProvider, G2PRegistryExternalDataPayload

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().init_logger()
        super().init_app()
        BaseExceptionHandler()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            _logger.info("Migrating database")

            # Data Models
            await G2PRegistryExternalDataProvider.create_migrate()
            await G2PRegistryExternalDataPayload.create_migrate()

        asyncio.run(migrate())
        


celery_app = Celery(
    "g2p_registry_example_beat_producer",
    broker=_config.celery_broker_url,
    backend=_config.celery_backend_url,
    include=["openg2p_registry_example_beat_producers.tasks"],
)

celery_app.conf.beat_schedule = {
    "g2p_registry_external_data_poller_beat_producer": {
        "task": "g2p_registry_external_data_poller_beat_producer",
        "schedule": timedelta(
            minutes=_config.g2p_celery_job_poll_frequency_minutes,
            hours=_config.g2p_celery_job_poll_frequency_hours,
            days=_config.g2p_celery_job_poll_frequency_days,
            weeks=_config.g2p_celery_job_poll_frequency_weeks,
        ),
    },
    "g2p_registry_external_data_ingester_beat_producer": {
        "task": "g2p_registry_external_data_ingester_beat_producer",
        "schedule": _config.g2p_celery_job_ingest_frequency,
    },
}
celery_app.conf.timezone = "UTC"
