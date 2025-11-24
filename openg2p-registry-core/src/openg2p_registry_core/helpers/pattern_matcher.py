import re
from typing import Tuple, Dict, Optional
from jsonpath_ng import parse as jsonpath_parse

from openg2p_fastapi_common.service import BaseService

from ..models import DataModel, IncomingModelSignaturePattern, IncomingModelSemanticPattern


class PatternMatcher(BaseService):
    """
    Pattern format:
        "<jsonpath><separator><regex>"
    Example:
        pattern_for_sender = "$.body.sender_name=>^PARTNER_[A-Z]+$"
        pattern_for_signature = "$.header.auth=>^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]*$"
        pattern_for_data_model = "$.body.meta.data_model_is=>^[A-Z]+$"
    """
    def __init__(self):
        super().__init__()
        self.separator: str = "=>"

    def get_signature_pattern_match(
        self, incoming_model_signature_pattern: IncomingModelSignaturePattern, data: Dict
    ) -> Tuple[str, str]:

        sender = self._extract_with_pattern(
            data, incoming_model_signature_pattern.pattern_for_sender
        )
        signature = self._extract_with_pattern(
            data, incoming_model_signature_pattern.pattern_for_signature
        )
        return sender, signature
    
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

    def _extract_jsonpath(self, data: Dict, jsonpath_expr: str) -> Optional[str]:
        expr = jsonpath_parse(jsonpath_expr)
        matches = expr.find(data)
        return matches[0].value if matches else None

    def _validate_regex(self, value: str, regex_expr: str) -> Optional[str]:
        pattern = re.compile(regex_expr)
        if not pattern.fullmatch(str(value)):
            return None
        return value
