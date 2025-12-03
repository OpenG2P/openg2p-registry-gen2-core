from sqlalchemy import String, Boolean, DateTime, Date, JSONB
from sqlalchemy.orm import Mapped, mapped_column, validates
from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_fastapi_common.models import BaseORMModel
from datetime import datetime, date


class G2PRegisterFamilyMemberBase(BaseORMModel):
    __abstract__ = True

    member_identifier: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    demographic_identifier: Mapped[str] = mapped_column(String, nullable=False, default_value="")

    name_prefix: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    name_given: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    name_surname: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    name_suffix: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    sex: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    birth_date: Mapped[date] = mapped_column(Date, nullable=True, default_value=None)

    related_persons: Mapped[JSONB] = mapped_column(JSONB, nullable=False, default_value=[])

    is_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default_value=False)
    marital_status: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    employment_status: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    occupation: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    income_level: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    education_level: Mapped[str] = mapped_column(String, nullable=False, default_value="")
    language_codes: Mapped[JSONB] = mapped_column(JSONB, nullable=False, default_value=[])
    additional_attributes: Mapped[JSONB] = mapped_column(JSONB, nullable=False, default_value={})

    registration_date: Mapped[date] = mapped_column(Date, nullable=False, default_value=datetime.now().date())
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False, default_value=datetime.now())


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
            self.name_prefix or "",
            self.name_given or "",
            self.name_surname or "",
            self.name_suffix or "",
            self.sex or "",
            self.birth_date or "",
            self.related_persons or "",
            self.is_disabled or "",
            self.marital_status or "",
            self.employment_status or "",
            self.occupation or "",
            self.income_level or "",
            self.education_level or "",
            self.language_codes or "",
            self.additional_attributes or ""
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