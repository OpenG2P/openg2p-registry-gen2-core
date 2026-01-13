from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="registry_core_", env_file=".env", extra="allow"
    )

    openapi_title: str = "OpenG2P Registry Core"
    openapi_description: str = """
        FastAPI Service for OpenG2P Registry Core
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    # MinIO Configuration
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "secret"
    minio_secure: bool = False
    minio_bucket_name: str = "templates"

    # Master Data Database Configuration
    master_data_db_driver: str = "postgresql+asyncpg"
    master_data_db_username: str = "postgres"
    master_data_db_password: str = "postgres"
    master_data_db_hostname: str = "localhost"
    master_data_db_port: int = 5432
    master_data_db_dbname: str = "openg2p_gen2_master_data_db"