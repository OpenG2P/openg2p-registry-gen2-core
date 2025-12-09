import httpx
from typing import Dict
from openg2p_fastapi_common.service import BaseService
from ..config import Settings

_config = Settings.get_config()

class WebsubHelper(BaseService):
    def __init__(self):
        super().__init__()
        self.websub_base_url = _config.websub_base_url
    
    def register_topic(self, topic: str):
        with httpx.Client() as client:
            url = f"{self.websub_base_url}/hub/"
            data = {
                "hub.mode": "register",
                "hub.topic": topic,
            }
            response = client.post(url, data=data)
            response.raise_for_status()
        
    def deregister_topic(self, topic: str):
        with httpx.Client() as client:
            url = f"{self.websub_base_url}/hub/"
            data = {
                "hub.mode": "deregister",
                "hub.topic": topic,
            }
            response = client.post(url, data=data)
            response.raise_for_status()
    
    def publish(self, topic: str, payload: Dict):
        with httpx.Client() as client:
            url = f"{self.websub_base_url}/hub/"
            headers = {
                "Content-Type": "application/json",
                "Link": f"<{self.websub_base_url}/hub/>; rel=\"hub\", <{topic}>; rel=\"self\""
            }
            data = {
                "hub.mode": "publish",
                "hub.topic": topic,
                "hub.content": payload
            }
            response = client.post(url, headers=headers, data=data)
            response.raise_for_status()
