import re
from typing import Tuple, Dict
from jsonpath_ng import parse as jsonpath_parse

from openg2p_fastapi_common.service import BaseService

from ..models import IncomingModelSignaturePattern


class SignaturePatternMatcher(BaseService):
    """
    Pattern format:
        "<jsonpath>::<regex>"
    Example:
        pattern_for_sender = "$.body.sender_name::^PARTNER_[A-Z]+$"
        pattern_for_signature = "$.header.auth.sign::^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]*$"
        pattern_for_data_model = "$.body.meta.data_model_is::^[A-Z]+$"
    """

    def match(
        self, incoming_model_signature_pattern: IncomingModelSignaturePattern, ingest_data: Dict
    ) -> Tuple[str, str]:

        sender = self._extract_with_pattern(
            ingest_data, incoming_model_signature_pattern.pattern_for_sender
        )
        signature = self._extract_with_pattern(
            ingest_data, incoming_model_signature_pattern.pattern_for_signature
        )
        return sender, signature


    def _extract_with_pattern(self, data: Dict, pattern_str: str):
        try:
            jsonpath_expr, regex_expr = pattern_str.split("::", 1)
            value = self._extract_jsonpath(data, jsonpath_expr)
            if value is None:
                return None
            return self._validate_regex(value, regex_expr)

        except ValueError:
            raise ValueError("Invalid pattern format")
        except Exception as e:
            raise e

    def _extract_jsonpath(self, data: Dict, jsonpath_expr: str):
        try:
            expr = jsonpath_parse(jsonpath_expr)
            matches = expr.find(data)
            return matches[0].value if matches else None
        except Exception as e:
            raise e
    
    def _validate_regex(self, value: str, regex_expr: str):
        try:
            pattern = re.compile(regex_expr)
            if not pattern.fullmatch(str(value)):
                return None
            return value
        except Exception as e:
            raise e
