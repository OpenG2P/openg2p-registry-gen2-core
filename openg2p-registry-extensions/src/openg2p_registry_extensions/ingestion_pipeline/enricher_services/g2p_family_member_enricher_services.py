import logging
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import select
from openg2p_registry_core.interfaces import G2PPayloadEnricherInterface
from openg2p_registry_extensions.register_domain.models import G2PRegisterFamilyMember


_logger = logging.getLogger('g2p-payload-enricher-service')

# DCI Payload Enrichers
class G2PDciFamilyMemberCreateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PDciFamilyMemberCreateEnricherService")

        parent_link_record_id = None

        # Try to find a parent family member using parent1_identifier
        parent1_identifier_data = data.get('parent1_identifier')
        if isinstance(parent1_identifier_data, dict):
            identifier_value = parent1_identifier_data.get('identifier_value')
            if identifier_value:
                _logger.debug(f"Checking for parent family member with parent1_identifier: {identifier_value}")
                parent_family_member = session.execute(
                    select(G2PRegisterFamilyMember).filter_by(member_identifier=identifier_value)
                ).scalar_one_or_none()

                if parent_family_member:
                    parent_link_record_id = parent_family_member.link_record_id
                    _logger.info(f"Found parent family member via parent1_identifier. Link record ID: {parent_link_record_id}")

        # If parent1_identifier didn't yield a result, try parent2_identifier
        if parent_link_record_id is None:
            parent2_identifier_data = data.get('parent2_identifier')
            if isinstance(parent2_identifier_data, dict):
                identifier_value = parent2_identifier_data.get('identifier_value')
                if identifier_value:
                    _logger.debug(f"Checking for parent family member with parent2_identifier: {identifier_value}")
                    parent_family_member = session.execute(
                        select(G2PRegisterFamilyMember).filter_by(member_identifier=identifier_value)
                    ).scalar_one_or_none()

                    if parent_family_member:
                        parent_link_record_id = parent_family_member.link_record_id
                        _logger.info(f"Found parent family member via parent2_identifier. Link record ID: {parent_link_record_id}")

        if parent_link_record_id:
            data['link_record_id'] = parent_link_record_id
        else:
            _logger.warning("Could not find a parent family member using either parent1_identifier or parent2_identifier.")
            data["link_record_id"] = None
        
        return data

class G2PDciFamilyMemberUpdateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PDciFamilyMemberUpdateEnricherService")
        return data

class G2PDciFamilyMemberDeleteEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PDciFamilyMemberDeleteEnricherService")
        return data

# SPDCI Payload Enrichers
class G2PSpdciFamilyMemberCreateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PSpdciFamilyMemberCreateEnricherService")
        return data

class G2PSpdciFamilyMemberUpdateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PSpdciFamilyMemberUpdateEnricherService")
        return data

class G2PSpdciFamilyMemberDeleteEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PSpdciFamilyMemberDeleteEnricherService")
        return data

# UNDP Payload Enrichers
class G2PUndpFamilyMemberCreateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PUndpFamilyMemberCreateEnricherService")
        return data

class G2PUndpFamilyMemberUpdateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PUndpFamilyMemberUpdateEnricherService")
        return data

class G2PUndpFamilyMemberDeleteEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PUndpFamilyMemberDeleteEnricherService")
        return data
