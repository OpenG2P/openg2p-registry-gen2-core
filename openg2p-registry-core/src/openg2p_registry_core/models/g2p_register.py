import enum
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Index, Date, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, validates
from openg2p_fastapi_common.models import BaseORMModel


class G2PRegister(BaseORMModel):
    __abstract__ = True

    internal_record_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    functional_record_id: Mapped[str] = mapped_column(String, nullable=True, unique=True, index=True)
    link_internal_record_id: Mapped[str] = mapped_column(String, nullable=True, index=True) # Link to internal_record_id of the parent
    link_foundational_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    record_name: Mapped[str] = mapped_column(String, nullable=True)
    record_image_storage_id: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    last_approved_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    last_approved_by: Mapped[str] = mapped_column(String, nullable=False)
    search_text: Mapped[str] = mapped_column(Text, nullable=True)

    def get_search_text_fields(self) -> list[str]:
        """Return G2PRegister fields for search text aggregation."""
        return [
            self.functional_record_id or "",
            self.record_name or "",
        ]

    @classmethod
    def __declare_last__(cls):
        """Create table-specific index and register event listeners after table is declared"""
        if not cls.__abstract__:
            # Create a unique index name based on the table name
            index_name = f"idx_{cls.__tablename__}_search_text_trigram"
            Index(index_name, cls.search_text, postgresql_using='gin', postgresql_ops={'search_text': 'gin_trgm_ops'}, table=cls.__table__)
            
            # Register event listeners for automatic search_text population
            @event.listens_for(cls, "before_insert")
            def populate_search_text_on_insert(mapper, connection, target):
                _populate_search_text(target)
            
            @event.listens_for(cls, "before_update")
            def populate_search_text_on_update(mapper, connection, target):
                _populate_search_text(target)


def _populate_search_text(target):
    """
    Populate search_text by aggregating fields from all parent classes
    that have get_search_text_fields() method.
    """
    all_fields = []
    # Collect fields from all classes in the MRO that have get_search_text_fields
    for base in target.__class__.__mro__:
        if hasattr(base, 'get_search_text_fields') and 'get_search_text_fields' in base.__dict__:
            # Call the method defined in this specific class
            fields = base.get_search_text_fields(target)
            all_fields.extend(fields)
    target.search_text = " ".join(filter(None, all_fields)).strip()

class MaritalStatusEnum(enum.Enum):
    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    DIVORCED = "DIVORCED"
    WIDOWED = "WIDOWED"
    SEPARATED = "SEPARATED"
    UNKNOWN = "UNKNOWN"

class GenderEnum(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHERS = "OTHERS"
    UNKNOWN = "UNKNOWN"

class G2PPerson(BaseORMModel):
    __abstract__ = True

    foundational_id: Mapped[str] = mapped_column(String, nullable=True, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    middle_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    given_name: Mapped[str] = mapped_column(String, nullable=True)
    prefix: Mapped[str] = mapped_column(String, nullable=True)
    suffix: Mapped[str] = mapped_column(String, nullable=True)
    gender: Mapped[GenderEnum] = mapped_column(String, nullable=True)
    birth_date: Mapped[str] = mapped_column(Date, nullable=True)
    phone_numbers: Mapped[list] = mapped_column(JSONB, nullable=True)
    emails: Mapped[list] = mapped_column(JSONB, nullable=True)
    marital_status: Mapped[MaritalStatusEnum] = mapped_column(String, nullable=True)
    occupation: Mapped[str] = mapped_column(String, nullable=True)
    income_level: Mapped[str] = mapped_column(String, nullable=True)
    language_code: Mapped[str] = mapped_column(String, nullable=True)
    education_level: Mapped[str] = mapped_column(String, nullable=True)
    registration_date: Mapped[str] = mapped_column(Date, nullable=True)

    def get_search_text_fields(self) -> list[str]:
        """Return G2PPerson fields for search text aggregation."""
        return [
            self.foundational_id or "",
            self.first_name or "",
            self.middle_name or "",
            self.last_name or "",
            self.given_name or "",
            self.gender.value if self.gender else "",
            str(self.birth_date) if self.birth_date else "",
            self.phone_numbers or "",
            self.emails or "",
            self.marital_status.value if self.marital_status else "",
            self.occupation or "",
            self.education_level or "",
        ]


class G2PGeo(BaseORMModel):
    __abstract__ = True

    latitude: Mapped[float] = mapped_column(String, nullable=True)
    longitude: Mapped[float] = mapped_column(String, nullable=True)
    altitude: Mapped[float] = mapped_column(String, nullable=True)
    plus_code: Mapped[str] = mapped_column(String, nullable=True, index=True)
    address_line_1: Mapped[str] = mapped_column(String, nullable=True)
    address_line_2: Mapped[str] = mapped_column(String, nullable=True)
    postal_code: Mapped[str] = mapped_column(String, nullable=True, index=True)
    country_code: Mapped[str] = mapped_column(String, nullable=True, index=True)
    geo_lowest_level_value_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    geo_code_hierarchy_json: Mapped[str] = mapped_column(JSONB, nullable=True)

    @validates('geo_lowest_level_value_id')
    def update_geo_hierarchy(self, _key: str, value: str) -> str:
        """
        Automatically populate geo_code_hierarchy_json when geo_lowest_level_value_id is set.
        Fetches the hierarchy from master-data-db with caching.
        """
        if value:
            from ..services import G2PGeoHierarchyService
            service = G2PGeoHierarchyService.get_component()
            self.geo_code_hierarchy_json = service.get_geo_hierarchy_sync(value)
        else:
            self.geo_code_hierarchy_json = None
        return value

    def get_search_text_fields(self) -> list[str]:
        """Return G2PGeo fields for search text aggregation."""
        fields = [
            self.plus_code or "",
            self.postal_code or "",
            self.country_code or "",
        ]
        # Extract searchable values from geo_code_hierarchy_json if present
        if self.geo_code_hierarchy_json and isinstance(self.geo_code_hierarchy_json, dict):
            hierarchy = self.geo_code_hierarchy_json.get("hierarchy", [])
            for level in hierarchy:
                if isinstance(level, dict):
                    fields.append(level.get("level_value_mnemonic", ""))
        return fields


class ShapeTypeEnum(enum.Enum):
    # TODO: Add remaining shape types as needed
    POINT = "POINT"
    LINESTRING = "LINESTRING"
    CIRCLE = "CIRCLE"
    BOX = "BOX"
    POLYGON = "POLYGON"
    MULTIPOINT = "MULTIPOINT"
    MULTILINESTRING = "MULTILINESTRING"
    MULTIPOLYGON = "MULTIPOLYGON"
    GEOMETRYCOLLECTION = "GEOMETRYCOLLECTION"

class G2PGeoShape(BaseORMModel):
    __abstract__ = True
    
    shape_type: Mapped[ShapeTypeEnum] = mapped_column(String, nullable=True) 
    shape_coordinates_json: Mapped[str] = mapped_column(JSONB, nullable=True)
    