from sqlalchemy import String, Date
from sqlalchemy.orm import Mapped, mapped_column, validates
from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegisterFarmerBase(BaseORMModel):
    __abstract__ = True

    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[str] = mapped_column(Date, nullable=False)
    address_line_1: Mapped[str] = mapped_column(String, nullable=False)
    address_line_2: Mapped[str] = mapped_column(String, nullable=True)
    geo_administrative_area_small: Mapped[str] = mapped_column(String, nullable=False)
    geo_administrative_area_large: Mapped[str] = mapped_column(String, nullable=False)
    post_code: Mapped[str] = mapped_column(String, nullable=False)

# All Register classes should have the prefix G2PRegister
class G2PRegisterFarmer(G2PRegisterFarmerBase, G2PRegister):
    __tablename__ = "g2p_register_farmers"

    @validates('first_name', 'last_name', 'address_line_1', 'address_line_2', 'geo_administrative_area_small', 'geo_administrative_area_large', 'post_code')
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
            self.first_name or "",
            self.last_name or "",
            self.address_line_1 or "",
            self.address_line_2 or "",
            self.geo_administrative_area_small or "",
            self.geo_administrative_area_large or "",
            self.post_code or ""
        ]
        self.search_text = " ".join(searchable_fields).strip()

# All Register History classes should have the prefix G2PRegisterHistory
class G2PRegisterHistoryFarmer(G2PRegisterFarmerBase, G2PRegisterHistory):
    __tablename__ = "g2p_register_history_farmers"
    pass
