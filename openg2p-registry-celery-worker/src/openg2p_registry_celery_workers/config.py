from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="registry_celery_workers_", env_file=".env", extra="allow"
    )
    openapi_title: str = "OpenG2P Registry Celery Workers"
    openapi_description: str = """
        Celery workers for OpenG2P Registry
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    # Registry Database
    db_driver: str = "postgresql"
    db_username: str = "postgres"
    db_password: str = "postgres"
    db_hostname: str = "localhost"
    db_port: int = 5432
    db_dbname: str = "registrydb"

    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"
    worker_queue: str = "registry_worker_queue"

    batch_size: int = 2000
    worker_max_attempts: int = 5

    # MinIO Configuration
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "secret"
    minio_secure: bool = False
    minio_bucket_name: str = "templates"
    

