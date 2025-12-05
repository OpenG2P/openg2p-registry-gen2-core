from sqlalchemy import String, Boolean, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy.dialects.postgresql import JSONB
from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_fastapi_common.models import BaseORMModel
from datetime import datetime, date


class G2PRegisterFamilyMemberBase(BaseORMModel):
    __abstract__ = True

    member_identifier: Mapped[str] = mapped_column(String, nullable=False)
    demographic_identifier: Mapped[str] = mapped_column(String, nullable=False)

    name_prefix: Mapped[str] = mapped_column(String, nullable=False)
    name_given: Mapped[str] = mapped_column(String, nullable=False)
    name_surname: Mapped[str] = mapped_column(String, nullable=False)
    name_suffix: Mapped[str] = mapped_column(String, nullable=False)
    sex: Mapped[str] = mapped_column(String, nullable=False)
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

    registration_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False)


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
            self.name_prefix,
            self.name_given,
            self.name_surname,
            self.name_suffix,
            self.sex,
            self.birth_date,
            self.related_persons or None,
            self.is_disabled or None,
            self.marital_status or None,
            self.employment_status or None,
            self.occupation or None,
            self.income_level or None,
            self.education_level or None,
            self.language_codes or None,
            self.additional_attributes or None
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