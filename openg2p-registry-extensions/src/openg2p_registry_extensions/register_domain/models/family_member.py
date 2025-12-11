from sqlalchemy import String, Boolean, DateTime, Date, Float
from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy.dialects.postgresql import JSONB
from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_fastapi_common.models import BaseORMModel
from datetime import datetime, date


class G2PRegisterFamilyMemberBase(BaseORMModel):
    
    __abstract__ = True

    # Identifiers
    identifier_type: Mapped[str] = mapped_column(String, nullable=True)
    identifier_value: Mapped[str] = mapped_column(String, nullable=True)

    # Name fields
    surname: Mapped[str] = mapped_column(String, nullable=True)
    given_name: Mapped[str] = mapped_column(String, nullable=True)
    second_name: Mapped[str] = mapped_column(String, nullable=True)
    prefix: Mapped[str] = mapped_column(String, nullable=True)
    suffix: Mapped[str] = mapped_column(String, nullable=True)

    # Contacts stored as JSON arrays
    phone_numbers: Mapped[list] = mapped_column(JSONB, nullable=True)
    emails: Mapped[list] = mapped_column(JSONB, nullable=True)

    # Basic details
    sex: Mapped[str] = mapped_column(String, nullable=True)
    birth_date: Mapped[str] = mapped_column(String, nullable=True)

    # Birthplace
    birth_place_name: Mapped[str] = mapped_column(String, nullable=True)
    birth_place_lat: Mapped[float] = mapped_column(Float, nullable=True)
    birth_place_lng: Mapped[float] = mapped_column(Float, nullable=True)

    # Death details
    death_date: Mapped[str] = mapped_column(String, nullable=True)
    death_place: Mapped[str] = mapped_column(String, nullable=True)

    # Address details
    address_line1: Mapped[str] = mapped_column(String, nullable=True)
    address_line2: Mapped[str] = mapped_column(String, nullable=True)
    locality: Mapped[str] = mapped_column(String, nullable=True)
    sub_region_code: Mapped[str] = mapped_column(String, nullable=True)
    region_code: Mapped[str] = mapped_column(String, nullable=True)
    postal_code: Mapped[str] = mapped_column(String, nullable=True)
    country_code: Mapped[str] = mapped_column(String, nullable=True)

    # Plus code + geolocation
    plus_code: Mapped[str] = mapped_column(String, nullable=True)
    geo_lat: Mapped[float] = mapped_column(Float, nullable=True)
    geo_lng: Mapped[float] = mapped_column(Float, nullable=True)

    # Marital info
    marital_status: Mapped[str] = mapped_column(String, nullable=True)
    marriage_date: Mapped[str] = mapped_column(String, nullable=True)
    divorce_date: Mapped[str] = mapped_column(String, nullable=True)

    # Parents
    parent1_identifier_value: Mapped[str] = mapped_column(String, nullable=True)
    parent2_identifier_value: Mapped[str] = mapped_column(String, nullable=True)



# All Register classes should have the prefix G2PRegister
class G2PRegisterFamilyMember(G2PRegisterFamilyMemberBase, G2PRegister):
    __tablename__ = "g2p_register_family_members"

    @validates('identifier_type', 'identifier_value', 'surname', 'given_name', 'second_name', 'prefix', 'suffix', 'phone_numbers', 'emails', 'sex', 'birth_date', 'birth_place_name', 'birth_place_lat', 'birth_place_lng', 'death_date', 'death_place', 'address_line1', 'address_line2', 'locality', 'sub_region_code', 'region_code', 'postal_code', 'country_code', 'plus_code', 'geo_lat', 'geo_lng', 'marital_status', 'marriage_date', 'divorce_date', 'parent1_identifier_value', 'parent2_identifier_value')
    def update_search_text(self, _key: str, value: str) -> str:
        """
        Automatically update search_text whenever any searchable field is modified.
        Combines all searchable fields into a single text for trigram search.
        """
        self._populate_search_text()
        return value

    def _populate_search_text(self) -> None:
        """
        Populate search_text by combining all searchable family member fields.
        """
        searchable_fields: list[str] = [
            # String fields - use 'or ""' for efficiency
            self.identifier_type or "",
            self.identifier_value or "",
            self.surname or "",
            self.given_name or "",
            self.second_name or "",
            self.prefix or "",
            self.suffix or "",
            self.sex or "",
            self.birth_place_name or "",
            self.death_date or "",
            self.death_place or "",
            self.address_line1 or "",
            self.address_line2 or "",
            self.locality or "",
            self.sub_region_code or "",
            self.region_code or "",
            self.postal_code or "",
            self.country_code or "",
            self.plus_code or "",
            self.marital_status or "",
            self.marriage_date or "",
            self.divorce_date or "",
            self.parent1_identifier_value or "",
            self.parent2_identifier_value or "",
            # Non-string fields - need str() conversion
            str(self.phone_numbers) if self.phone_numbers else "",
            str(self.emails) if self.emails else "",
            str(self.birth_date) if self.birth_date else "",
            str(self.birth_place_lat) if self.birth_place_lat is not None else "",
            str(self.birth_place_lng) if self.birth_place_lng is not None else "",
            str(self.geo_lat) if self.geo_lat is not None else "",
            str(self.geo_lng) if self.geo_lng is not None else "",
        ]
        self.search_text = " ".join(searchable_fields).strip()

# All Register History classes should have the prefix G2PRegisterHistory
class G2PRegisterHistoryFamilyMember(G2PRegisterFamilyMemberBase, G2PRegisterHistory):
    __tablename__ = "g2p_register_history_family_members"

    # Override all columns from G2PRegisterFamilyMemberBase to make them nullable for history
    identifier_type: Mapped[str] = mapped_column(String, nullable=True)
    identifier_value: Mapped[str] = mapped_column(String, nullable=True)
    surname: Mapped[str] = mapped_column(String, nullable=True)
    given_name: Mapped[str] = mapped_column(String, nullable=True)
    second_name: Mapped[str] = mapped_column(String, nullable=True)
    prefix: Mapped[str] = mapped_column(String, nullable=True)
    suffix: Mapped[str] = mapped_column(String, nullable=True)
    phone_numbers: Mapped[list] = mapped_column(JSONB, nullable=True)
    emails: Mapped[list] = mapped_column(JSONB, nullable=True)
    sex: Mapped[str] = mapped_column(String, nullable=True)
    birth_date: Mapped[str] = mapped_column(String, nullable=True)
    birth_place_name: Mapped[str] = mapped_column(String, nullable=True)
    birth_place_lat: Mapped[float] = mapped_column(Float, nullable=True)
    birth_place_lng: Mapped[float] = mapped_column(Float, nullable=True)
    death_date: Mapped[str] = mapped_column(String, nullable=True)
    death_place: Mapped[str] = mapped_column(String, nullable=True)
    address_line1: Mapped[str] = mapped_column(String, nullable=True)
    address_line2: Mapped[str] = mapped_column(String, nullable=True)
    locality: Mapped[str] = mapped_column(String, nullable=True)
    sub_region_code: Mapped[str] = mapped_column(String, nullable=True)
    region_code: Mapped[str] = mapped_column(String, nullable=True)
    postal_code: Mapped[str] = mapped_column(String, nullable=True)
    country_code: Mapped[str] = mapped_column(String, nullable=True)
    plus_code: Mapped[str] = mapped_column(String, nullable=True)
    geo_lat: Mapped[float] = mapped_column(Float, nullable=True)
    geo_lng: Mapped[float] = mapped_column(Float, nullable=True)
    marital_status: Mapped[str] = mapped_column(String, nullable=True)
    marriage_date: Mapped[str] = mapped_column(String, nullable=True)
    divorce_date: Mapped[str] = mapped_column(String, nullable=True)
    parent1_identifier_value: Mapped[str] = mapped_column(String, nullable=True)
    parent2_identifier_value: Mapped[str] = mapped_column(String, nullable=True)