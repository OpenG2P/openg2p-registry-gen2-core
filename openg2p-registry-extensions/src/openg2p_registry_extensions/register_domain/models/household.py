from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, validates
from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegisterHouseholdBase(BaseORMModel):
    __abstract__ = True

    household_name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=True)


# All Register classes should have the prefix G2PRegister
class G2PRegisterHousehold(G2PRegisterHouseholdBase, G2PRegister):
    __tablename__ = "g2p_register_households"

    @validates('household_name', 'address')
    def update_search_text(self, _key: str, value: str) -> str:
        """
        Automatically update search_text whenever any searchable field is modified.
        Combines all searchable fields into a single text for trigram search.
        """
        self._populate_search_text()
        return value

    def _populate_search_text(self) -> None:
        """
        Populate search_text by combining all searchable fields.
        """
        searchable_fields: list[str] = [
            self.household_name or "",
            self.address or ""
        ]
        self.search_text = " ".join(searchable_fields).strip()


# All Register History classes should have the prefix G2PRegisterHistory
class G2PRegisterHistoryHousehold(G2PRegisterHouseholdBase, G2PRegisterHistory):
    __tablename__ = "g2p_register_history_households"

    # Override all columns from base to make them nullable for history
    household_name: Mapped[str] = mapped_column(String, nullable=True)
    address: Mapped[str] = mapped_column(String, nullable=True)

