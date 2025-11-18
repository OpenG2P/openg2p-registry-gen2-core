import re
from sqlalchemy import select
from typing import Tuple, Dict, List
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

    async def match(self, ingest_data: Dict, session) -> Tuple[
        IncomingModelSignaturePattern, str, str, str
    ]:
        patterns: List[IncomingModelSignaturePattern] = await self._get_all_model_signature_patterns(session)

        for pattern in patterns:
            # If ANY one of the three doesn't match -> try next pattern
            sender = self._extract_with_pattern(
                ingest_data, pattern.pattern_for_sender
            )
            if sender is None:
                continue

            signature = self._extract_with_pattern(
                ingest_data, pattern.pattern_for_signature
            )
            if signature is None:
                continue

            data_model = self._extract_with_pattern(
                ingest_data, pattern.pattern_for_data_model
            )
            if data_model is None:
                continue

            # TODO: Check weather sender matches the partner_mnemonic stored in db for this pattern
            # partner_mnemonic = await self._get_partner_mnemonic(pattern.partner_id, session)
            # if partner_mnemonic != sender:
            #     continue
            
            # If ALL three matched -> pattern found
            return (pattern, sender, signature, data_model)

        # No match found
        return (None, None, None, None)


    async def _get_all_model_signature_patterns(
        self, session
    ) -> List[IncomingModelSignaturePattern]:

        patterns = await session.execute(select(IncomingModelSignaturePattern))
        return patterns.scalars().all()

    def _extract_with_pattern(self, data: Dict, pattern_str: str):
        try:
            jsonpath_expr, regex_expr = pattern_str.split("::", 1)
        except ValueError:
            raise ValueError("Invalid pattern format")

        value = self._extract_jsonpath(data, jsonpath_expr)
        if value is None:
            return None

        try:
            pattern = re.compile(regex_expr)
        except Exception as e:
            raise e

        if not pattern.fullmatch(str(value)):
            return None

        return value

    def _extract_jsonpath(self, data: Dict, jsonpath_expr: str):
        try:
            expr = jsonpath_parse(jsonpath_expr)
            matches = expr.find(data)
            return matches[0].value if matches else None
        except Exception as e:
            raise e

    # TODO: Add this logic after partner models are established
    # async def _get_partner_mnemonic(self, partner_id: str, session: Session) -> str:
    #     pass