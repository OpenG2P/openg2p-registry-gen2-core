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

    @validates('name_prefix', 'name_given', 'name_surname', 'name_suffix', 'sex', 'birth_date', 'related_persons', 'is_disabled', 'marital_status', 'employment_status', 'occupation', 'income_level', 'education_level', 'language_codes', 'additional_attributes', 'registration_date', 'last_updated')
    def update_search_text(self, _key: str, value: str) -> str:
        """
        Automatically update search_text whenever any searchable field is modified.
        Combines all searchable fields into a single text for trigram search.
        """
        self._populate_search_text()
        return value

    def _populate_search_text(self) -> None:
        """
        Populate search_text by combining all searchable farmer fields.
        """
        searchable_fields: list[str] = [
            # String fields - use 'or ""' for efficiency
            self.name_prefix or "",
            self.name_given or "",
            self.name_surname or "",
            self.name_suffix or "",
            self.sex or "",
            self.marital_status or "",
            self.employment_status or "",
            self.occupation or "",
            self.income_level or "",
            self.education_level or "",
            # Non-string fields - need str() conversion
            str(self.birth_date) if self.birth_date else "",
            str(self.related_persons) if self.related_persons else "",
            str(self.is_disabled) if self.is_disabled is not None else "",
            str(self.language_codes) if self.language_codes else "",
            str(self.additional_attributes) if self.additional_attributes else ""
        ]
        self.search_text = " ".join(searchable_fields).strip()

# All Register History classes should have the prefix G2PRegisterHistory
class G2PRegisterHistoryFamilyMember(G2PRegisterFamilyMemberBase, G2PRegisterHistory):
    __tablename__ = "g2p_register_history_family_members"

    # Override all columns from G2PRegisterFamilyMemberBase to make them nullable for history
    name_prefix: Mapped[str] = mapped_column(String, nullable=True)
    name_given: Mapped[str] = mapped_column(String, nullable=True)
    name_surname: Mapped[str] = mapped_column(String, nullable=True)
    name_suffix: Mapped[str] = mapped_column(String, nullable=True)
    sex: Mapped[str] = mapped_column(String, nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=True)
    related_persons: Mapped[JSONB] = mapped_column(JSONB, nullable=True)
    is_disabled: Mapped[bool] = mapped_column(Boolean, nullable=True)
    marital_status: Mapped[str] = mapped_column(String, nullable=True)
    employment_status: Mapped[str] = mapped_column(String, nullable=True)
    occupation: Mapped[str] = mapped_column(String, nullable=True)
    income_level: Mapped[str] = mapped_column(String, nullable=True)
    education_level: Mapped[str] = mapped_column(String, nullable=True)
    language_codes: Mapped[JSONB] = mapped_column(JSONB, nullable=True)
    additional_attributes: Mapped[JSONB] = mapped_column(JSONB, nullable=True)
    registration_date: Mapped[date] = mapped_column(Date, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=True)