import enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DciStatusCode(enum.Enum):
    RECEIVED = "rcvd"
    PENDING = "pdng"
    SUCCESS = "succ"
    REJECTED = "rjct"


class DciSearchResultData(BaseModel):
    """
    SearchResponse.data

    Search result record as an outcome of search/subscribe action.
    """
    version: str = Field(
        default="1.0.0",
        description="Schema version (default 1.0.0)",
    )
    # reg_type: str = Field(
    #     description="Registry type, e.g. ns:org:RegistryType:Civil",
    # )
    # reg_event_type: str = Field(
    #     description="Registry event type, e.g. spdci-common:RegistryEventType:LiveBirth",
    # )
    # reg_record_type: str = Field(
    #     description="Record type, as per notify_record_type in SubscribeRequest",
    # )
    reg_records: List[Dict[str, Any]] = Field(
        description="List of matching registry records (JSON-LD Person/Member objects)",
    )


class DciSearchResultPagination(BaseModel):
    """
    SearchResponse.search_response[i].pagination
    """
    page_size: int = Field(
        description="Number of records per page",
    )
    page_number: int = Field(
        description="Current page number (1-based in examples)",
    )
    total_count: Optional[int] = Field(
        default=None,
        description="Total number of records matching query (if provided)",
    )


class DciSearchResponseItem(BaseModel):
    """
    One entry in SearchResponse.search_response[]
    """
    reference_id: str = Field(
        description="Reference id from corresponding SearchRequest",
        max_length=99,
    )
    timestamp: str = Field(
        description="ISO-8601 timestamp (same semantics as message_ts)",
    )
    status: str = Field(
        description='Enum: "rcvd" "pdng" "succ" "rjct"',
    )
    status_reason_code: Optional[str] = Field(
        default=None,
        description="SearchStatusReasonCode (optional)",
    )
    status_reason_message: Optional[str] = Field(
        default=None,
        description=(
            "Status reason code message. Helps actionable messaging "
            "for systems / end users (<= 999 chars)"
        ),
        max_length=999,
    )
    data: Optional[DciSearchResultData] = Field(
        default=None,
        description="Search result record as an outcome of search/subscribe action",
    )
    pagination: Optional[DciSearchResultPagination] = Field(
        default=None,
        description="Per-reference pagination info (page, size, total_count)",
    )
    locale: Optional[str] = Field(
        default=None,
        description="Locale, e.g. 'en'",
        max_length=10,
    )


class DciSearchResponse(BaseModel):
    """
    components/schemas/SearchResponse

    (The structure is inferred from how TxnStatusResponse references it.)
    """
    transaction_id: str = Field(
        description=(
            "transaction_id set by txn initiating system to correlate all related "
            "requests in a business transaction (<= 99 chars)"
        ),
        max_length=99,
    )
    correlation_id: str = Field(
        description=(
            "correlation_id acknowledged by the processing system to correlate "
            "related requests (<= 99 chars)"
        ),
        max_length=99,
    )
    search_response: List[DciSearchResponseItem] = Field(
        description="Array of search result entries",
        min_length=1,
    )


# --- Envelope for /registry/on-search ---------------------------------------
# Reuse your existing DciResponseHeader and DciEncryptedMessage definitions.
# Shown here just as type references:

class DciResponseHeader(BaseModel):
    version: str = "1.0.0"
    message_id: str
    message_ts: str
    action: str
    sender_id: str
    receiver_id: str
    sender_uri: Optional[str] = None
    status: Optional[str] = None
    status_reason_code: Optional[str] = None
    status_reason_message: Optional[str] = None
    total_count: Optional[int] = None
    completed_count: Optional[int] = None
    is_msg_encrypted: bool = False
    meta: Dict[str, Any] = Field(default_factory=dict)


class DciEncryptedMessage(BaseModel):
    header: Dict[str, Any]
    ciphertext: str
    encrypted_key: str
    tag: str
    iv: str


class DciSearchResponseEnvelope(BaseModel):
    """
    Request body schema for POST /registry/on-search

    {
      "signature": "...",
      "header": { ... MessageHeader ... },
      "message": { ... SearchResponse ... } | { ... EncryptedMessage ... }
    }
    """
    signature: str = Field(
        description='MsgSignature: signature of {header}+{message}',
    )
    header: DciResponseHeader = Field(
        description="Message header",
    )
    message: Union[DciSearchResponse, DciEncryptedMessage] = Field(
        description="SearchResponse (plain) or EncryptedMessage",
    )
