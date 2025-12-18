import re
import json
from typing import Tuple, Dict, Optional, Any
from jsonpath_ng import parse as jsonpath_parse

from openg2p_fastapi_common.service import BaseService

from ..models import DataModel, IncomingModelKeyPath, IncomingModelSemanticPattern


class PatternMatcher(BaseService):
    """
    Pattern format:
        "<jsonpath><separator><regex>"
    Example:
        key_path_for_sender = "$.body.sender_name"
        key_path_for_signature = "$.header.auth"
        key_path_for_signature_payload = "$.body.message.payload"
        key_path_for_business_payload = "$.body.message.payload.business_payload"
        pattern_for_data_model = "$.body.meta.data_model_is=>^[A-Z]+$"
    """
    def __init__(self):
        super().__init__()
        self.separator: str = "=>"

    def get_signature_pattern_path(
        self, incoming_model_key_path: IncomingModelKeyPath, data: Dict
    ) -> Tuple[str, str, Dict]:

        sender = self._extract_jsonpath(
            data, incoming_model_key_path.key_path_for_sender
        )
        signature = self._extract_jsonpath(
            data, incoming_model_key_path.key_path_for_signature
        )
        signature_payload = self._extract_jsonpath(
            data, incoming_model_key_path.key_path_for_signature_payload
        )
        return sender, signature, signature_payload
    
    def get_business_payload(
        self, incoming_model_semantic_pattern: IncomingModelSemanticPattern, data: Dict
    ) -> Optional[Dict]:
        business_payload = self._extract_jsonpath(
            data, incoming_model_semantic_pattern.key_path_for_business_payload
        )

        if business_payload is None:
            return None

        if isinstance(business_payload, dict):
            return business_payload

        if isinstance(business_payload, str):
            business_payload = business_payload.strip()
            if not business_payload:
                return None
            try:
                return json.loads(business_payload)
            except json.JSONDecodeError:
                raise ValueError(f"Business payload is not valid JSON: {business_payload}")

        raise TypeError(f"Unsupported business_payload type: {type(business_payload)}")
    
    def get_data_model_pattern_match(
        self, data_model: DataModel, data: Dict
    ) -> str:
        data_model_mnemonic = self._extract_with_pattern(
            data, data_model.pattern_for_data_model
        )
        return data_model_mnemonic

    def validate_semantic_pattern_match(
        self, incoming_model_semantic_pattern: IncomingModelSemanticPattern, data: Dict
    ) -> bool:
        register = self._extract_with_pattern(
            data, incoming_model_semantic_pattern.pattern_for_register
        )
        operation = self._extract_with_pattern(
            data, incoming_model_semantic_pattern.pattern_for_operation
        )
        if register and operation:
            return True

        return False

    def get_ingest_data_list_elements_path_expr(
        self, incoming_model_key_path: IncomingModelKeyPath, data: Dict
    ) -> Tuple[list, Any]:
        expr = self._get_parsed_jsonpath_expr(
            incoming_model_key_path.key_path_for_list_elements
        )
        elements = self._extract_jsonpath(
            data, incoming_model_key_path.key_path_for_list_elements
        )

        return elements, expr

    def _extract_with_pattern(self, data: Dict, pattern: str) -> Optional[str]:
        try:
            jsonpath_expr, regex_expr = pattern.split(self.separator, 1)
            value = self._extract_jsonpath(data, jsonpath_expr)
            if value is None:
                return None
            return self._validate_regex(value, regex_expr)

        except ValueError:
            raise ValueError("Invalid pattern format")
        except Exception as e:
            raise e

    def _extract_jsonpath(self, data: Dict, jsonpath_expr: str) -> Optional[Any]:
        expr = jsonpath_parse(jsonpath_expr)
        matches = expr.find(data)
        return matches[0].value if matches else None

    def _validate_regex(self, value: str, regex_expr: str) -> Optional[str]:
        pattern = re.compile(regex_expr)
        if not pattern.fullmatch(str(value)):
            return None
        return value
    
    def _get_parsed_jsonpath_expr(self, pattern: str) -> Any:
        return jsonpath_parse(pattern)
