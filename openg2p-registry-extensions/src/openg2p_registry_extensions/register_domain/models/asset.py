from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, validates
from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegisterAssetBase(BaseORMModel):
    __abstract__ = True

    asset_name: Mapped[str] = mapped_column(String, nullable=False)
    asset_type: Mapped[str] = mapped_column(String, nullable=True)
    asset_value: Mapped[float] = mapped_column(Float, nullable=True)


# All Register classes should have the prefix G2PRegister
class G2PRegisterAsset(G2PRegisterAssetBase, G2PRegister):
    __tablename__ = "g2p_register_assets"

    @validates('asset_name', 'asset_type')
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
            self.asset_name or "",
            self.asset_type or ""
        ]
        self.search_text = " ".join(searchable_fields).strip()


# All Register History classes should have the prefix G2PRegisterHistory
class G2PRegisterHistoryAsset(G2PRegisterAssetBase, G2PRegisterHistory):
    __tablename__ = "g2p_register_history_assets"

    # Override all columns from base to make them nullable for history
    asset_name: Mapped[str] = mapped_column(String, nullable=True)
    asset_type: Mapped[str] = mapped_column(String, nullable=True)
    asset_value: Mapped[float] = mapped_column(Float, nullable=True)

