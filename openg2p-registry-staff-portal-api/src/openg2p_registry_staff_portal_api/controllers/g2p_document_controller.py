import logging
from typing import List
from fastapi import UploadFile, File, Form

from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PDocumentControllerService
from openg2p_registry_core.schemas import (
    UploadDocumentsResponse, UploadDocumentsResponseData
)

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PDocumentController(BaseController):
    """
    Controller for handling document-related operations.
    Provides endpoints for uploading and managing documents for change requests.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["G2P Documents"]
        self.g2p_document_controller_service = G2PDocumentControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/documents"

        self.router.add_api_route(
            "/upload",
            self.upload_documents,
            responses={200: {"model": UploadDocumentsResponse}},
            methods=["POST"],
        )

    async def upload_documents(
        self,
        section_id: str = Form(..., description="Section ID to validate document labels against"),
        document_label_ids: List[str] = Form(..., description="List of document label IDs (one per file)"),
        files: List[UploadFile] = File(..., description="List of files to upload")
    ) -> UploadDocumentsResponse:
        """
        Upload documents for a change request to MinIO storage.

        Files are uploaded and stored in MinIO. Returns document_store_ids that can be
        used when creating a change request with documents.

        The number of document_label_ids must match the number of files.
        """
        try:
            if len(document_label_ids) != len(files):
                raise ValueError(f"Number of document_label_ids ({len(document_label_ids)}) must match number of files ({len(files)})")

            # Pair each file with its document_label_id
            files_with_labels = list(zip(document_label_ids, files))

            upload_response_data: UploadDocumentsResponseData = await self.g2p_document_controller_service.upload_documents(
                section_id=section_id,
                files=files_with_labels
            )
            upload_response: UploadDocumentsResponse = self.helper.construct_upload_documents_success_response(
                upload_response_data=upload_response_data
            )
            return upload_response
        except Exception as error_exception:
            _logger.error(f"Error in upload_documents: {str(error_exception)}")
            error_response: UploadDocumentsResponse = self.helper.construct_upload_documents_error_response(error_exception)
            return error_response

