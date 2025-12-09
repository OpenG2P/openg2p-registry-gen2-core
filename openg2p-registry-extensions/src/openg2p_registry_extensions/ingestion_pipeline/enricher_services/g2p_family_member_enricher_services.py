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

        related_member_identifier: str | None = None
        if 'related_person' in data and isinstance(data['related_person'], list):
            for person in data['related_person']:
                if person['relationship_type'].lower() == 'parent' and \
                    'related_member' in person and \
                    isinstance(person['related_member'], dict):

                    related_member_data = person['related_member']
                    if 'member_identifier' in related_member_data:
                        related_member_identifier = related_member_data['member_identifier']
                        break

        if related_member_identifier:
            related_member = session.execute(
                select(G2PRegisterFamilyMember).filter(G2PRegisterFamilyMember.member_identifier == related_member_identifier)
            ).scalar_one_or_none()
            if related_member:
                _logger.info(f"Found related_member link_record_id: { related_member.link_record_id }")
                data['link_record_id'] = related_member.link_record_id
        
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
