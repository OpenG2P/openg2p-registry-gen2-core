import logging
from typing import Dict
from sqlalchemy.orm import Session

from openg2p_registry_core.interfaces import G2PPayloadEnricherInterface
from openg2p_registry_extensions.register_domain.models import G2PRegisterFamilyMember


_logger = logging.getLogger('g2p-payload-enricher-service')

# DCI Payload Enrichers
class G2PDciFamilyMemberCreateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PDciFamilyMemberCreateEnricherService")

        related_member_identifiers = []
        if 'related_person' in data and isinstance(data['related_person'], list):
            for person in data['related_person']:
                if 'related_member' in person and isinstance(person['related_member'], dict):
                    related_member_data = person['related_member']
                    if 'member_identifier' in related_member_data:
                        related_member_identifiers.append(related_member_data['member_identifier'])
                    elif 'spdci:member_identifier' in related_member_data:
                        related_member_identifiers.append(related_member_data['spdci:member_identifier'])        

        if related_member_identifiers:
            link_record_ids = [
                member.link_record_id
                for member in session.query(G2PRegisterFamilyMember)
                .filter(G2PRegisterFamilyMember.member_identifier.in_(related_member_identifiers))
                .all()
            ]
            _logger.info(f"Found link_record_ids: {link_record_ids}")
        
        if link_record_ids:
            data['spdci:link_record_id'] = link_record_ids[0]

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
