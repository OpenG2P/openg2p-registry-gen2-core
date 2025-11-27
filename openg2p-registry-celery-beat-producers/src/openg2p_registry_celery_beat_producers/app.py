# ruff: noqa: E402

import logging

from .config import Settings
_config = Settings.get_config()

from celery import Celery
from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.exception import BaseExceptionHandler

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().init_logger()
        super().init_app()
        BaseExceptionHandler()


celery_app = Celery(
    "g2p_registry_celery_beat_producer",
    broker=_config.celery_broker_url,
    backend=_config.celery_backend_url,
    include=["openg2p_registry_celery_beat_producers.tasks"],
)

celery_app.conf.beat_schedule = {
    "raw_data_classification_beat_producer": {
        "task": "raw_data_classification_beat_producer",
        "schedule": _config.raw_data_classification_beat_producer_frequency,
    },
    "data_transformation_beat_producer": {
        "task": "data_transformation_beat_producer",
        "schedule": _config.data_transformation_beat_producer_frequency,
    },
    "data_ingestion_beat_producer": {
        "task": "data_ingestion_beat_producer",
        "schedule": _config.data_ingestion_beat_producer_frequency,
    },
    "deduplication_register_beat_producer": {
        "task": "deduplication_register_beat_producer",
        "schedule": _config.deduplication_beat_producer_frequency,
    },
    "deduplication_changelog_beat_producer": {
        "task": "deduplication_changelog_beat_producer",
        "schedule": _config.deduplication_beat_producer_frequency,
    },
}
celery_app.conf.timezone = "UTC"
