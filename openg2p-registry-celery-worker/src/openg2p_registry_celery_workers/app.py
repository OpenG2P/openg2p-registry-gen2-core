# ruff: noqa: E402

import logging

from .config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)

from celery import Celery
from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.exception import BaseExceptionHandler
from openg2p_registry_core.helpers import MinioClient, TemplateHelper


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().init_logger()
        super().init_app()
        BaseExceptionHandler()

        # Utils
        MinioClient(
            _config.minio_endpoint,
            _config.minio_access_key,
            _config.minio_secret_key,
            _config.minio_secure,
            _config.minio_bucket_name,
        )
        TemplateHelper()

celery_app = Celery(
    "g2p_registry_celery_worker",
    broker=_config.celery_broker_url,
    backend=_config.celery_backend_url,
    include=["openg2p_registry_celery_workers.tasks"],
)

celery_app.conf.timezone = "UTC"
