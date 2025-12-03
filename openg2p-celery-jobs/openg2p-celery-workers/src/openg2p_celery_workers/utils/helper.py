from abc import ABC, abstractmethod
from requests import Response
from typing import Dict
from ..utils import (
    CrvsHelper
)


class HelperInterface(ABC):
    """
    Interface for helper classes
    Helper naming convention: <helper_code>Helper
    Example: CrvsHelper, DciHelper, UndpHelper
    """
    @abstractmethod
    def get_polling_response(self, polling_url: str) -> Response:
        pass

    @abstractmethod
    def post_ingest_request(
        self,
        data_model: str,
        request_payload: Dict,
        request_headers: Dict,
    ) -> Response:
        pass

class HelperFactory:
    @staticmethod
    def get_helper(helper_type: str) -> HelperInterface:
        if helper_type.lower() == "crvs":
            return CrvsHelper()
        raise NotImplementedError(f"Helper for {helper_type} is not implemented")
