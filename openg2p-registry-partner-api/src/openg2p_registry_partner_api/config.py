from openg2p_registry_extensions.config import Settings as ExtSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(ExtSettings):
    model_config = SettingsConfigDict(
        env_prefix="registry_partner_api_", env_file=".env", extra="allow"
    )

    openapi_title: str = "OpenG2P Registry Partner API"
    openapi_description: str = """
        FastAPI Service for OpenG2P Registry Partner API
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    # Registry Database
    db_username: str = "postgres"
    db_password: str = "password"
    db_hostname: str = "localhost"
    db_port: int = 5432
    db_dbname: str = "registrydb"

    # Keymanager settings
    keymanager_api_base_url: str = ""
    keymanager_api_timeout: int = 10
    keymanager_api_domain: str = "AUTH"
    keymanager_ssl_verify: bool = False
    keymanager_auth_enabled: bool = False
    keymanager_auth_url: str = ""
    keymanager_auth_client_id: str = "openg2p-registry-partner"
    keymanager_auth_client_secret: str = ""
    keymanager_sign_app_id: str = "REGISTRY"
    keymanager_sign_ref_id: str = ""

