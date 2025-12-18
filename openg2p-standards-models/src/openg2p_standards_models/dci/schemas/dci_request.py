from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class DciQueryValue(BaseModel):
    expression: str = Field(..., description="Query expression, e.g. GraphQL string used for registry search",)

class DciQuery(BaseModel):
    type: str = Field(..., description='Type of query, e.g. "ns:org:QueryType:graphql"',)
    value: DciQueryValue

class DciSortItem(BaseModel):
    attribute_name: str
    sort_order: Literal["asc", "desc"]

class DciPagination(BaseModel):
    page_size: int = Field(..., ge=1)
    page_number: int = Field(..., ge=1)

class DciPurpose(BaseModel):
    text: Optional[str] = None
    code: Optional[str] = Field(None, description="From a fixed set, documented at ref_uri",)
    ref_uri: Optional[str] = Field(None, description="URI to provide more info on codes",)

class DciConsent(BaseModel):
    # In spec this is actually JSON-LD; we just capture useful fields here
    context: Optional[str] = Field(None, alias="@context", description="JSON-LD context, e.g. Consent.jsonld URI",)
    type_: Optional[str] = Field(None, alias="@type", description='JSON-LD type, typically "Consent"',)
    ts: Optional[str] = Field(None, description="Timestamp, same type as MsgHeader.message_ts",)
    purpose: Optional[DciPurpose] = None

    class Config:
        validate_by_name = True

class DciAuthorize(BaseModel):
    context: Optional[str] = Field(None, alias="@context", description="JSON-LD context, e.g. Authorize.jsonld URI",)
    type_: Optional[str] = Field(None, alias="@type", description='JSON-LD type, typically "Authorize"',)
    ts: Optional[str] = Field(None, description="Timestamp, same type as MsgHeader.message_ts",)
    purpose: Optional[DciPurpose] = None

    class Config:
        validate_by_name = True

class DciSearchCriteria(BaseModel):
    version: str = "1.0.0"
    reg_type: str = Field(..., description='Registry type, e.g. "ns:org:RegistryType:Civil"',)
    reg_event_type: str = Field(..., description='Registry event type, e.g. "spdci-common:RegistryEventType:LiveBirth"',)
    query_type: str = Field(..., description='e.g. "expression"',)
    query: DciQuery
    sort: Optional[List[DciSortItem]] = None
    pagination: Optional[DciPagination] = None
    consent: Optional[DciConsent] = None
    authorize: Optional[DciAuthorize] = None


class DciSearchRequestItem(BaseModel):
    reference_id: str = Field(..., max_length=99, description="Unique reference for this individual search within the txn")
    timestamp: Optional[str] = Field(None, description="Timestamp of this individual request (format per implementation)")
    search_criteria: DciSearchCriteria
    locale: Optional[str] = Field("en", description="Locale for response, e.g. 'en'",)


class DciSearchRequest(BaseModel):
    transaction_id: str = Field(..., max_length=99, description=(
        "Transaction id set by the initiating system to correlate all related "
        "requests in a business transaction."
    ))
    search_request: List[DciSearchRequestItem] = Field(..., description="Batch of individual search requests", min_items=1)


class DciRequestHeader(BaseModel):
    version: str = Field(..., description="API header version")
    message_id: str = Field(..., max_length=99, description="Unique ID for this message")
    message_ts: str = Field(..., description="Timestamp of the message, ISO-8601 or epoch")
    action: str = Field(..., description="Action being performed, e.g., 'search'")
    sender_id: str = Field(..., description="Unique ID of the sender system")
    sender_uri: Optional[str] = Field(None, description="Callback or endpoint URI of the sender")
    receiver_id: str = Field(..., description="Unique ID of the receiver system")
    total_count: Optional[int] = Field(None, description="Total number of messages in this transaction if batched")
    is_msg_encrypted: bool = Field(False, description="Indicates if the message body is encrypted")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata object")


class DciSearchRequestEnvelope(BaseModel): # This class already has the Dci prefix.
    signature: str = Field(..., description="Signature of {header}+{message} body verified using sender's signing public key")
    header: DciRequestHeader
    message: DciSearchRequest
