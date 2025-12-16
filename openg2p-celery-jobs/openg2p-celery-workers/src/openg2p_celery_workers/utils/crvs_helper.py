import math
import uuid
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime
import requests
from requests import Response

from openg2p_celery_job_models.models import G2PExternalDataProvider

from ..config import Settings
from .helper import HelperInterface

_config = Settings.get_config()

class CrvsHelper(HelperInterface):
    def __init__(self):
        self.registry_ingest_url = _config.registry_ingest_url
    
    def create_polling_request(self, page_number: int, page_size: int = 1) -> Tuple[Dict, Dict]:
        
        current_utc_iso = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'

        request_body: Dict[str, Any] = {
            "header": {
                "version": "1.0.0",
                "message_id": uuid.uuid4().hex,
                "message_ts": current_utc_iso,
                "action": "search",
                "sender_id": "spp.example.org",
                "sender_uri": "https://spp.example.org/{namespace}/callback/on-search",
                "receiver_id": "civilregistry.example.org",
                "is_msg_encrypted": False,
                "meta": {}
            },
            "message": {
                "transaction_id": uuid.uuid4().hex,
                "search_request": [
                    {
                        "reference_id": uuid.uuid4().hex,
                        "timestamp": current_utc_iso,
                        "search_criteria": {
                            "version": "1.0.0",
                            "reg_type": "ns:org:RegistryType:Civil",
                            "reg_record_type": "spdci-extensions-dci:Person",
                            "query_type": "expression",
                            "query": {
                                "type": "ns:org:QueryType:graphql",
                                "value": {
                                    "expression": "GeBirthRecordById {\n  person(UIN: \"1\") {\n    BRN\n    name\n    gender\n    birthDate\n    birthPlace\n    parents\n  }\n}\n"
                                }
                            },
                            "sort": [
                                {
                                    "attribute_name": "poverty_score",
                                    "sort_order": "asc"
                                }
                            ],
                            "pagination": {
                                "page_size": page_size,
                                "page_number": page_number
                            },
                            "consent": {
                                "@context": "https://schema.spdci.org/common/v1/api-schemas/Consent.jsonld",
                                "@type": "Consent",
                                "ts": current_utc_iso,
                                "purpose": {
                                    "text": {
                                        "type": "string"
                                    },
                                    "code": {
                                        "type": "string",
                                        "description": "From a fixed set, documented at refUri"
                                    },
                                    "ref_uri": {
                                        "type": "string",
                                        "format": "uri",
                                        "description": "Uri to provide more info on consent codes"
                                    }
                                }
                            },
                            "authorize": {
                                "@context": "https://schema.spdci.org/common/v1/api-schemas/Authorize.jsonld",
                                "@type": "Authorize",
                                "ts": current_utc_iso,
                                "purpose": {
                                    "text": {
                                        "type": "string"
                                    },
                                    "code": {
                                        "type": "string",
                                        "description": "From a fixed set, documented at refUri"
                                    },
                                    "ref_uri": {
                                        "type": "string",
                                        "format": "uri",
                                        "description": "Uri to provide more info on authorize codes"
                                    }
                                }
                            }
                        },
                        "locale": "en"
                    }
                ]
            }
        }
        request_header = {}

        return request_header, request_body

    def send_polling_request(
        self, 
        data_provider: G2PExternalDataProvider,
    ) -> List[Response]:
        # Mock response for testing
        mock_response_data = {
            "signature": "Signature:  namespace=\"spdci\", kidId=\"{sender_id}|{unique_key_id}|{algorithm}\", algorithm=\"ed25519\", created=\"1606970629\", expires=\"1607030629\", headers=\"(created) (expires) digest\", signature=\"Base64(signing content)",
            "header": {
                "version": "1.0.0",
                "message_id": "789",
                "message_ts": "",
                "action": "on-search",
                "status": "rcvd",
                "status_reason_code": "rjct.version.invalid",
                "status_reason_message": "string",
                "total_count": 1,
                "completed_count": 1,
                "sender_id": "civilregistry.example.org",
                "receiver_id": "registry.example.org",
                "is_msg_encrypted": False,
                "meta": {}
            },
            "message": {
                "transaction_id": 123456789,
                "correlation_id": "9876543210",
                "search_response": [
                {
                    "reference_id": "12345678901234567890",
                    "timestamp": "",
                    "status": "rcvd",
                    "status_reason_code": "rjct.reference_id.invalid",
                    "status_reason_message": "string",
                    "data": {
                    "version": "1.0.0",
                    "reg_type": "ns:org:RegistryType:Civil",
                    "reg_record_type": "spdci-extensions-dci:Person",
                    "reg_records": [
                        {
                        "@context": {
                            "@vocab": "https://schema.spdci.org/common/v1",
                            "xsd": "http://www.w3.org/2001/XMLSchema#",
                            "schema": "http://schema.org/",
                            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                            "owl": "http://www.w3.org/2002/07/owl#"
                        },
                        "@id": "CRVS_Person_3",
                        "@type": "CRVS_Person",
                        "identifier": {
                            "@id": "Identifier",
                            "@type": "Identifier",
                            "identifier_type": "UIN",
                            "identifier_value": "197382465"
                        },
                        "name": {
                            "@type": "Name",
                            "surname": "Martinez",
                            "given_name": "Elena",
                            "second_name": "",
                            "prefix": "Dr.",
                            "suffix": "PhD"
                        },
                        "phone_number": [
                            "+34612345678"
                        ],
                        "email": [
                            "elena.martinez@example.com"
                        ],
                        "sex": "female",
                        "birth_date": "1980-03-23T10:20:15",
                        "birth_place": {
                            "name": "hospital/Madrid_Central",
                            "geo": {
                            "@type": "GeoCoordinates",
                            "latitude": 9.5604,
                            "longitude": 100.0245
                            },
                            "address_line": "",
                            "contained_in_place": "",
                            "contains_place": [
                            {
                                "@id": "Place_3",
                                "@type": "Place",
                                "name": "Pattaya Floating Market",
                                "address": "Bophut Koh Samui Surat Thani 84320 Thailand",
                                "geo": {
                                "@type": "GeoCoordinates",
                                "latitude": 9.5617,
                                "longitude": 100.0259
                                }
                            }
                            ]
                        },
                        "death_date": "",
                        "death_place": "",
                        "address": {
                            "@id": "Address_1",
                            "@type": "Address",
                            "address_line1": "Bophut Koh Samui",
                            "address_line2": "Surat, Near Big Buddha Beach",
                            "locality": "Thani",
                            "sub_region_code": "SH",
                            "region_code": "A205",
                            "postal_code": "84320",
                            "country_code": "TH",
                            "geo_location": {
                            "@id": "GeoLocation_1",
                            "@type": "GeoLocation",
                            "plus_code": {
                                "global_code": "8FW4V900+",
                                "geometry": {
                                "@id": "geometry",
                                "@type": "GeoLocation",
                                "bounds": {
                                    "@id": "bounds",
                                    "@type": "geometry",
                                    "northeast": {
                                    "@id": "northeast",
                                    "@type": "GeoCoordinates",
                                    "latitude": 48.900000000000006,
                                    "longitude": 2.4000000000000057
                                    },
                                    "southwest": {
                                    "@id": "southwest",
                                    "@type": "GeoCoordinates",
                                    "latitude": 48.849999999999994,
                                    "longitude": 2.3499999999999943
                                    }
                                },
                                "location": {
                                    "@id": "location",
                                    "@type": "GeoCoordinates",
                                    "latitude": 48.875,
                                    "longitude": 2.375
                                }
                                }
                            }
                            }
                        },
                        "marital_status": "S",
                        "marriage_date": "",
                        "divorce_date": "",
                        "parent1_identifier": {
                            "@id": "Identifier",
                            "@type": "Identifier",
                            "identifier_type": "UIN",
                            "identifier_value": "537564821"
                        },
                        "parent2_identifier": {
                            "@id": "Identifier",
                            "@type": "Identifier",
                            "identifier_type": "UIN",
                            "identifier_value": "564582793"
                        }
                        }
                    ]
                    },
                    "pagination": {
                    "page_size": 1,
                    "page_number": 1,
                    "total_count": 1
                    },
                    "locale": "en"
                }
                ]
            }
        }
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = json.dumps(mock_response_data).encode('utf-8')
        mock_response.headers['Content-Type'] = 'application/json'

        return [mock_response]

        if data_provider.polling_url is None:
            raise Exception(f"Polling URL is not configured for {data_provider.provider_name} data provider")

        responses: List[Response] = []
        
        try:
            _, initial_default_body = self.create_polling_request(data_provider, page_number=1)
            pagination_path = initial_default_body.get("message", {}).get("search_request", [{}])[0].get("search_criteria", {}).get("pagination")
            original_page_size = pagination_path.get("page_size", 1) if pagination_path else 1 # Default to 1 if not found

            request_header_initial, request_body_initial = self.create_polling_request(data_provider, page_number=1, page_size=1)
            # NOTE: sign the `request_body_initial` here
            request_body_initial["signature"] = "some_signature_value" # Placeholder for actual signature
            initial_response = requests.post(
                data_provider.polling_url,
                headers=request_header_initial,
                json=request_body_initial,
                timeout=10,
            )
            initial_response.raise_for_status()
            responses.append(initial_response)

            initial_response_data = initial_response.json()
            total_count = initial_response_data.get("header", {}).get("total_count")
            
            if total_count is None:
                return responses
            
            actual_page_size = original_page_size if original_page_size > 0 else 1 
            
            num_pages = math.ceil(total_count / actual_page_size)
            
            if num_pages <= 1:
                 return responses

            for page_number in range(1, num_pages + 1):
                if page_number == 1 and actual_page_size >= total_count:
                    continue

                request_header_paginated, request_body_paginated = self.create_polling_request(data_provider, page_number=page_number, page_size=actual_page_size)
                # NOTE: sign the `request_body_paginated` here
                request_body_paginated["signature"] = "some_signature_value" # Placeholder for actual signature
                response = requests.post(
                    data_provider.polling_url,
                    headers=request_header_paginated,
                    json=request_body_paginated,
                    timeout=10,
                )
                response.raise_for_status()
                responses.append(response)

            return responses

        except requests.exceptions.RequestException as req_e:
            raise Exception(f"Network or request error calling polling_url: {str(req_e)}")
        except Exception as e:
            raise Exception(f"Error during polling attempt: {str(e)}")
    
    def enrich_polling_response(self, response_body: Dict[str, Any]) -> Dict[str, Any]:
        query = self._get_operation_query()
        response_body["query"] = query

        return response_body

    def _get_operation_query(self) -> Dict[str, Any]:
        return {
            "type": "ns:org:QueryType:graphql",
            "value": {
                "expression": "GeBirthRecordById {\n  person(UIN: \"1\") {\n    BRN\n    name\n    gender\n    birthDate\n    birthPlace\n    parents\n  }\n}\n"
            }
        }
