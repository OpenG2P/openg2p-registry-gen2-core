import logging
import requests
from requests import Response
from typing import Tuple, Dict, List
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from openg2p_celery_job_models.models import (
    StatusEnum, 
    G2PRegistryExternalDataProvider,
    G2PRegistryExternalDataPayload,
)

from ..app import celery_app
from ..config import Settings
from ..engine import Engine
from ..utils import HelperFactory, HelperInterface

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = Engine.get_engine()


@celery_app.task(name="g2p_registry_external_data_poller_worker")
def g2p_registry_external_data_poller_worker(provider_id: str):
    _logger.info(f"Processing g2p_registry_external_data_poller_worker")
    session_maker = sessionmaker(
        bind=_engine, expire_on_commit=False
    )

    with session_maker() as session:
        g2p_registry_external_data_provider: G2PRegistryExternalDataProvider | None = None
        
        try:
            g2p_registry_external_data_provider = session.get(G2PRegistryExternalDataProvider, provider_id)

            polling_helper: HelperInterface = HelperFactory.get_helper(g2p_registry_external_data_provider.helper_code)
            
            # TODO: currently assuming a signle data item per page is returned
            poll_responses: List[Response] = polling_helper.get_polling_response(
                g2p_registry_external_data_provider,
            )
            _logger.info(
                f"Successfully received data item from {g2p_registry_external_data_provider.polling_url} for provider_id {provider_id}."
            )

            for poll_response in poll_responses:
                if poll_response.status_code == 200:
                    response_body, response_headers = _get_response_body_headers(poll_response)

                    g2p_registry_external_data_payload = G2PRegistryExternalDataPayload(
                        provider_id=provider_id,
                        payload_json=response_body,
                        payload_headers=response_headers,
                        process_status=StatusEnum.PENDING.value,
                        created_at=func.now()
                    )
                    session.add(g2p_registry_external_data_payload)

                    g2p_registry_external_data_provider.poll_latest_error_code = None
                    g2p_registry_external_data_provider.poll_latest_datetime = func.now()
                    g2p_registry_external_data_provider.poll_latest_success_datetime = func.now()

                else:
                    raise Exception(
                        f"List reponse threw error with status code: {poll_response.status_code}"
                        )
            
            session.commit()

        # TODO: Handel this inside the helper
        # except requests.exceptions.RequestException as req_e:
        #     _logger.error(
        #         f"Network or request error calling polling_url {g2p_registry_external_data_provider.polling_url} for provider_id {provider_id}: {str(req_e)}"
        #     )
        #     session.rollback()
        #     g2p_registry_external_data_provider.poll_latest_error_code = str(req_e)
        #     g2p_registry_external_data_provider.poll_latest_datetime = func.now()
        #     session.commit()

        except Exception as e:
            _logger.error(
                f"Error during processing g2p_registry_external_data_poller_worker for provider_id {provider_id}: {str(e)}"
            )
            session.rollback()

            g2p_registry_external_data_provider.poll_latest_error_code = str(e)
            g2p_registry_external_data_provider.poll_latest_datetime = func.now()

            session.commit()
            # Raise exception for testing
            raise e

        _logger.info(
            f"Completed processing g2p_registry_external_data_poller_worker for provider_id: {provider_id}"
        )


def _get_response_body_headers(response: requests.Response) -> Tuple[Dict, Dict]:

    response_body: Dict = response.json() if response.content else {}
    response_headers: Dict = dict(response.headers)

    return response_body, response_headers