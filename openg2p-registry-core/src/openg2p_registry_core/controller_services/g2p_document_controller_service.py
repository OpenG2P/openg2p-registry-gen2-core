import logging
from openg2p_fastapi_common.service import BaseService

from ..services import G2PRegisterService
from ..schemas import UploadDocumentsResponseData

_logger = logging.getLogger('g2p-document-controller-service')


class G2PDocumentControllerService(BaseService):
    """
    Controller service for handling document-related operations.
    This service acts as an intermediary between the controller and the register service
    for all document upload and management operations.
    """

    async def upload_documents(
        self,
        section_id: str,
        files: list  # List of (document_label_id, UploadFile) tuples
    ) -> UploadDocumentsResponseData:
        """
        Upload documents to MinIO storage.

        Args:
            section_id: The section ID to validate document labels against
            files: List of tuples containing (document_label_id, UploadFile)

        Returns:
            UploadDocumentsResponseData with list of uploaded document info
        """
        _logger.info(f"Uploading {len(files)} documents for section_id: {section_id}")
        g2p_register_service = G2PRegisterService.get_component()
        upload_response: UploadDocumentsResponseData = await g2p_register_service.upload_documents(
            section_id=section_id,
            files=files
        )
        return upload_response

