from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, validates
from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_fastapi_common.models import BaseORMModel
import uuid


class G2PRegisterFamilyBase(BaseORMModel):
    __abstract__ = True

    family_id: Mapped[str] = mapped_column(String, nullable=False)
    family_name: Mapped[str] = mapped_column(String, nullable=False)

# All Register classes should have the prefix G2PRegister
class G2PRegisterFamily(G2PRegisterFamilyBase, G2PRegister):
    __tablename__ = "g2p_register_families"

    @validates('family_id', 'family_name')
    def update_search_text(self, _key: str, value: str) -> str:
        """
        Automatically update search_text whenever any searchable field is modified.
        Combines all searchable fields into a single text for trigram search.
        """
        self._populate_search_text()
        return value

    def _populate_search_text(self) -> None:
        """
        Populate search_text by combining all searchable family fields.
        """
        searchable_fields: list[str] = [
            self.family_id or "",
            self.family_name or ""
        ]
        self.search_text = " ".join(searchable_fields).strip()

# All Register History classes should have the prefix G2PRegisterHistory
class G2PRegisterHistoryFamily(G2PRegisterFamilyBase, G2PRegisterHistory):
    __tablename__ = "g2p_register_history_families"

    # Override all columns from G2PRegisterFamilyBase to make them nullable for history
    family_id: Mapped[str] = mapped_column(String, nullable=True)
    family_name: Mapped[str] = mapped_column(String, nullable=True)