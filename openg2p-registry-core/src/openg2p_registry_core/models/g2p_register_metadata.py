import uuid
import re
import enum

from sqlalchemy import Boolean, Integer, String, Text, JSON, Float, Index, text
from sqlalchemy.orm import Mapped, mapped_column, validates
from openg2p_fastapi_common.models import BaseORMModel

class RegisterPurposeEnum(enum.Enum):
    REGISTER = "REGISTER"
    PROGRAM_REGISTER = "PROGRAM_REGISTER"
    TABLE = "TABLE"

class G2PRegisterDefinition(BaseORMModel):
    __tablename__ = "g2p_register_definitions"

    register_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    register_mnemonic: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    register_subject: Mapped[str] = mapped_column(String, nullable=True)
    register_description: Mapped[Text] = mapped_column(Text, nullable=True)
    master_register_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    register_rank: Mapped[int] = mapped_column(Integer, nullable=True)

    # Register type flags
    register_purpose: Mapped[RegisterPurposeEnum] = mapped_column(String, nullable=False)
    program_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    program_mnemonic: Mapped[str] = mapped_column(String, nullable=True, index=True)

    # Register display configuration
    register_icon: Mapped[str] = mapped_column(Text, nullable=True)  # BASE64 encoded icon
    has_image: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Deduplication configuration
    dedup_is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dedup_threshold_score: Mapped[float] = mapped_column(Float, nullable=True)

    @validates('register_mnemonic')
    def set_register_subject(self, _key: str, register_mnemonic_value: str) -> str:
        """
        Automatically set register_subject to the plural form of register_mnemonic
        with the first letter capitalized.
        Example: 'farmer' -> 'Farmers'
        """
        if register_mnemonic_value:
            plural_form: str = register_mnemonic_value + 's'
            capitalized_plural: str = plural_form[0].upper() + plural_form[1:]
            self.register_subject = capitalized_plural
        return register_mnemonic_value


class G2PRegisterUITab(BaseORMModel):
    __tablename__ = "g2p_register_ui_tabs"

    tab_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    register_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    tab_label: Mapped[str] = mapped_column(String, nullable=False)
    tab_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_for_new_intake_form: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    no_of_verifications_required: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    intake_form_name: Mapped[str] = mapped_column(String, nullable=True)
    intake_form_description: Mapped[str] = mapped_column(String, nullable=True)
    intake_form_auto_approve: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    @validates('tab_label')
    def validate_tab_label(self, _key: str, tab_label_value: str) -> str:
        """
        Validate that tab_label is lowercase and uses underscores (no spaces or special characters).
        Example valid: 'personal_info', 'contact_details'
        Example invalid: 'Personal Info', 'contact-details', 'ContactDetails'
        """
        if tab_label_value:
            pattern: str = r'^[a-z][a-z0-9_]*$'
            if not re.match(pattern, tab_label_value):
                raise ValueError(
                    f"tab_label must be lowercase with underscores only. "
                    f"Got: '{tab_label_value}'. Example valid: 'personal_info'"
                )
        return tab_label_value
