from typing import Optional, List, Any, Literal, Union
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator, Field
from enum import Enum

from ..models import ApprovalStatusEnum


# =============================================================================
# Filter Types and Schemas (GraphQL-style filtering with security)
# =============================================================================

class FilterOperator(str, Enum):
    """Supported filter operators."""
    # Equality
    EQ = "eq"
    NEQ = "neq"
    # List
    IN = "in"
    NIN = "nin"
    # String
    CONTAINS = "contains"
    NCONTAINS = "ncontains"
    STARTS_WITH = "startsWith"
    ENDS_WITH = "endsWith"
    # Comparison
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    # Null
    IS_NULL = "isNull"


class FilterCondition(BaseModel):
    """
    Single field filter with operators.
    Supports GraphQL-style filtering like: {"field": {"eq": "value"}}
    """
    eq: Optional[Any] = None
    neq: Optional[Any] = None
    in_: Optional[List[Any]] = Field(default=None, alias="in")
    nin: Optional[List[Any]] = None
    contains: Optional[str] = None
    ncontains: Optional[str] = None
    startsWith: Optional[str] = None
    endsWith: Optional[str] = None
    gt: Optional[Any] = None
    gte: Optional[Any] = None
    lt: Optional[Any] = None
    lte: Optional[Any] = None
    isNull: Optional[bool] = None

    class Config:
        populate_by_name = True

    @model_validator(mode='after')
    def check_max_operators(self):
        """Security: Limit operators per field to prevent DoS."""
        MAX_OPERATORS = 3
        non_null_count = sum(
            1 for field_name in self.model_fields.keys()
            if getattr(self, field_name if field_name != 'in_' else 'in_') is not None
        )
        if non_null_count > MAX_OPERATORS:
            raise ValueError(f"Maximum {MAX_OPERATORS} operators per field allowed")
        return self


class FilterSchemaFieldOption(BaseModel):
    """Option for dropdown filter type."""
    value: str
    label: str


class FilterSchemaField(BaseModel):
    """
    Schema definition for a filterable field.
    This is stored in filter_schema and tells the frontend what filters are available.
    """
    field_name: str
    display_label: str
    filter_type: Literal["dropdown", "text", "date_range", "number_range", "boolean"]
    order: int
    allowed_operators: List[str]
    options: Optional[List[FilterSchemaFieldOption]] = None  # For dropdown with static options
    options_source: Optional[str] = None  # "distinct" to fetch from DB

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "field_name": "approval_status",
                    "display_label": "Status",
                    "filter_type": "dropdown",
                    "order": 1,
                    "allowed_operators": ["eq", "in"],
                    "options": [
                        {"value": "PENDING", "label": "Pending"},
                        {"value": "APPROVED", "label": "Approved"}
                    ]
                },
                {
                    "field_name": "date_of_birth",
                    "display_label": "Date of Birth",
                    "filter_type": "date_range",
                    "order": 2,
                    "allowed_operators": ["eq", "gte", "lte", "gt", "lt"]
                },
                {
                    "field_name": "first_name",
                    "display_label": "First Name",
                    "filter_type": "text",
                    "order": 3,
                    "allowed_operators": ["eq", "contains", "startsWith", "endsWith"]
                }
            ]
        }


class RegisterPayload(BaseModel):
    pass


class RegisterSummaryData(BaseModel):
    register_id: str
    register_mnemonic: str
    register_subject: Optional[str] = None
    total_record_count: int


class ChangeRequestSummaryData(BaseModel):
    total_count: int
    approved_count: int
    pending_count: int


class RegisterData(BaseModel):
    register_id: str
    register_mnemonic: str
    register_subject: Optional[str] = None
    register_description: Optional[str] = None
    master_register_id: Optional[str] = None


class ChildRegisterData(BaseModel):
    register_id: str
    register_mnemonic: str
    register_subject: Optional[str] = None
    register_description: Optional[str] = None


class RegisterUITabData(BaseModel):
    tab_id: str
    register_id: str
    tab_label: str
    tab_order: int


class DisplayField(BaseModel):
    field_name: str
    value: Optional[str] = None
    order: int


class SearchResultData(BaseModel):
    internal_record_id: str
    functional_record_id: str
    link_record_id: Optional[str] = None
    record_name: Optional[str] = None
    image: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    last_approved_at: Optional[str] = None
    last_approved_by: Optional[str] = None
    display_fields: Optional[List[DisplayField]] = None

    class Config:
        from_attributes: bool = True


class RecordData(BaseModel):
    """
    Record data with flattened additional fields.
    Extra fields from the register implementation table are included at root level.
    """
    model_config = ConfigDict(extra="allow", from_attributes=True)

    internal_record_id: str
    functional_record_id: str
    link_record_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    last_approved_at: Optional[str] = None
    last_approved_by: Optional[str] = None


class ChangeRequestSearchResultData(BaseModel):
    change_request_id: str
    register_id: str
    tab_id: str
    internal_record_id: str
    section_id: str
    source_partner_id: str
    created_by: str
    created_at: Optional[str] = None
    no_of_verifications_required: Optional[int] = None
    no_of_verifications_done: Optional[int] = None
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    change_payload: Optional[dict] = None

    class Config:
        from_attributes: bool = True

class BaseChangePayload(BaseModel):
    internal_record_id: str

class ChangePayload(BaseChangePayload):
    class Config:
        from_attributes: bool = True
        extra = "allow"  # Allow extra fields to be preserved and accessible


class ChangeRequestRequestPayload(RegisterPayload):
    """Request payload for creating/updating change requests - sent from Partners"""
    register_id: Optional[str] = None
    register_mnemonic: Optional[str] = None
    tab_id: Optional[str] = None
    section_id: Optional[str] = None
    section_register_id: Optional[str] = None
    change_payload: Optional[ChangePayload] = None
    change_payload_array: Optional[List[ChangePayload]] = None
    # For approve/reject operations
    change_request_id: Optional[str] = None
    rejection_reason: Optional[str] = None


class ChangeRequestResponsePayload(RegisterPayload):
    """Response payload for change requests - returned to clients"""
    register_id: Optional[str] = None
    tab_id: Optional[str] = None
    section_id: Optional[str] = None
    section_register_id: Optional[str] = None

    no_of_verifications_required: Optional[int] = 0
    no_of_verifications_done: Optional[int] = 0
    approval_status: ApprovalStatusEnum = ApprovalStatusEnum.PENDING
    change_request_id: Optional[str] = None
    internal_record_id: Optional[str] = None

    created_by: Optional[str] = None
    created_at: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


class NumberOfVersionsData(BaseModel):
    register_id: str
    internal_record_id: str
    number_of_versions: int
    last_updated_by: Optional[str] = None
    last_updated_at: Optional[datetime] = None
    last_approved_by: Optional[str] = None
    last_approved_at: Optional[datetime] = None


class NumberOfPendingChangeRequestsData(BaseModel):
    subject_register_id: str
    subject_record_id: str
    tab_id: str
    number_of_pending_change_requests: int


class NumberOfCrossRegisterChangesData(BaseModel):
    subject_register_id: str
    subject_record_id: str
    number_of_cross_register_changes: int


class CrossRegisterChangeRequestData(BaseModel):
    change_request_id: str
    register_id: str
    register_mnemonic: str
    tab_id: str
    tab_label: str
    internal_record_id: str
    section_id: str
    source_partner_id: str
    created_by: str
    created_at: Optional[str] = None
    no_of_verifications_required: Optional[int] = None
    no_of_verifications_done: Optional[int] = None
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    class Config:
        from_attributes: bool = True


class CrossRegisterChangesData(BaseModel):
    cross_register_changes: list["CrossRegisterChangeRequestData"]


class ChangeRequestData(BaseModel):
    change_request_id: str
    register_id: str
    tab_id: str
    internal_record_id: str
    section_id: str
    source_partner_id: str
    created_by: str
    created_at: Optional[str] = None
    no_of_verifications_required: Optional[int] = None
    no_of_verifications_done: Optional[int] = None
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    change_payload: Optional[dict] = None

    class Config:
        from_attributes: bool = True


class ChangeRequestsData(BaseModel):
    change_requests: List[ChangeRequestData]

    class Config:
        from_attributes: bool = True


class VerificationData(BaseModel):
    verification_id: str
    register_id: str
    internal_record_id: str
    section_id: str
    change_request_id: str
    verified_by: str
    verified_at: Optional[str] = None
    verification_observations: Optional[str] = None
    is_approved: bool

    class Config:
        from_attributes: bool = True


class VerificationsData(BaseModel):
    verifications: List[VerificationData]

    class Config:
        from_attributes: bool = True


class AddVerificationPayload(BaseModel):
    change_request_id: str
    verification_observations: Optional[str] = None
    is_approved: bool


class DeduplicationRegisterResultData(BaseModel):
    """Deduplication result for a change request against a register record."""
    dedup_result_id: str
    change_request_id: str
    internal_record_id: str
    match_score: float
    field_matches: dict
    created_at: Optional[str] = None

    class Config:
        from_attributes: bool = True


class DeduplicationChangerequestResultData(BaseModel):
    """Deduplication result for a change request against another change request."""
    dedup_result_id: str
    change_request_id: str
    candidate_change_request_id: str
    match_score: float
    field_matches: dict
    created_at: Optional[str] = None

    class Config:
        from_attributes: bool = True


class DeduplicationRegisterResultsData(BaseModel):
    """List of deduplication results for a change request against register records."""
    results: List[DeduplicationRegisterResultData]

    class Config:
        from_attributes: bool = True


class DeduplicationChangerequestResultsData(BaseModel):
    """List of deduplication results for a change request against other change requests."""
    results: List[DeduplicationChangerequestResultData]

    class Config:
        from_attributes: bool = True


class IngestDataPayload(BaseModel):
    correlation_id: str


class RegisterSchemaData(BaseModel):
    """Schema data for a register including deduplication, search result, and filter configurations."""
    register_id: str
    deduplicate_schema: Optional[List[dict]] = None
    search_result_schema: Optional[List[dict]] = None
    filter_schema: Optional[List[dict]] = None

    class Config:
        from_attributes: bool = True


class RegisterSectionData(BaseModel):
    """Section data for a register representing UI schema for a section."""
    section_register_id: str
    register_id: str
    section_id: str
    tab_id: str
    section_mnemonic: str
    section_description: Optional[str] = None
    documents_required: bool = False
    no_of_verifications_required: int = 0
    auto_approval: bool = False
    is_list: bool = False
    section_ui_schema: Optional[dict] = None

    class Config:
        from_attributes: bool = True


class RegisterTabRecordData(BaseModel):
    """
    Records for a single section_register_id within a tab.
    Multiple sections with the same section_register_id are deduplicated.
    """
    section_register_id: str
    records: List[RecordData]