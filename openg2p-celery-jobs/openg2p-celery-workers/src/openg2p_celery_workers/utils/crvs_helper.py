from fastapi import Request
from typing import Dict, Optional, List, Tuple, DateTime
from datetime import datetime
import requests
from requests import Response

from openg2p_registry_example_models.models import G2PRegistryExternalDataProvider

from ..config import Settings
from ..utils import HelperInterface


_config = Settings.get_config()

class CrvsHelper(HelperInterface):
    def __init__(self):
        self.registry_ingest_url = _config.registry_ingest_url
    
    def get_polling_response(
        self, 
        data_provider: G2PRegistryExternalDataProvider,
    ) -> List[Response]:
        if(data_provider.polling_url is None):
            raise Exception(f"Polling URL is not configured for {data_provider.provider_name} data provider")
        
        start_datetime, end_datetime = self._get_polling_datetime_range(data_provider.poll_latest_datetime)
        
        # TODO: Request logic subject to change 
        request_params = {"start_datetime": start_datetime, "end_datetime": end_datetime}
        
        try:
            response = requests.post(
                data_provider.polling_url,
                params=request_params,
                timeout=30,
            )
            return [response]

        except requests.exceptions.RequestException as req_e:
            raise Exception(f"Network or request error calling polling_url: {str(req_e)}")
        except Exception as e:
            raise Exception(f"Error occured during polling attempt: {str(e)}")
    
    def post_ingest_request(
        self,
        data_model: str,
        request_body: Dict,
        request_headers: Dict,
    ) -> Response:
        params = {"data_model": data_model}
        try:
            response = requests.post(
                self.registry_ingest_url,
                json=request_body,
                headers=request_headers,
                params=params,
                timeout=30,
            )
            return response

        except requests.exceptions.RequestException as req_e:
            raise Exception(f"Network or request error calling registry ingest endpoint: {str(req_e)}")
        except Exception as e:
            raise Exception(f"Error occured processing ingest request: {str(e)}")

    def _get_polling_datetime_range(
        self,
        poll_latest_datetime: DateTime,
    ) -> Tuple[DateTime, DateTime]:
        start_datetime: DateTime = datetime.fromisoformat(_config.entry_point_start_datetime)
        end_datetime: DateTime = datetime.now()

        if poll_latest_datetime is not None:
            start_datetime = poll_latest_datetime
        
        return start_datetime, end_datetime