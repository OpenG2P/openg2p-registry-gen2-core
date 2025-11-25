from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="registry_celery_beat_", env_file=".env", extra="allow"
    )
    openapi_title: str = "OpenG2P Registry Celery Beat Producers"
    openapi_description: str = """
        Celery Beat Producers for OpenG2P Registry
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    # Registry Database
    db_driver: str = "postgresql"
    db_username: str = "postgres"
    db_password: str = "password"
    db_hostname: str = "localhost"
    db_port: int = 5432
    db_dbname: str = "registrydb"

    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"
    worker_queue: str = "registry_worker_queue"

    batch_size: int = 2000
    raw_data_classification_beat_producer_frequency: int = 20
    data_transformation_beat_producer_frequency: int = 20
    data_ingestion_beat_producer_frequency: int = 20
    no_of_tasks_to_process: int = 4
