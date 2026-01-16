import logging
from openg2p_fastapi_common.service import BaseService

from .. helpers import MinioClient
from ..services import G2PRegisterService
from ..schemas import (
    UploadDocumentsResponseData,
    UploadRecordImageData,
    DocumentLabelsForSectionData,
    SectionDocumentsData,
    ChangeRequestDocumentsData,
    GetDocumentLabelsForSectionRequest,
    GetSectionDocumentsRequest,
    GetSectionDocumentsForChangeRequestRequest,
    FileUrlRequest, FileUrlData
)

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

    async def upload_record_image(
        self,
        section_id: str,
        file  # UploadFile
    ) -> UploadRecordImageData:
        """
        Upload a record image to MinIO storage.

        Args:
            section_id: The section ID (for organizing storage path)
            file: The image file to upload

        Returns:
            UploadRecordImageData with document_store_id and filename
        """
        _logger.info(f"Uploading record image for section_id: {section_id}")
        g2p_register_service = G2PRegisterService.get_component()
        upload_response: UploadRecordImageData = await g2p_register_service.upload_record_image(
            section_id=section_id,
            file=file
        )
        return upload_response

    async def get_document_labels_for_section(
        self,
        request: GetDocumentLabelsForSectionRequest
    ) -> DocumentLabelsForSectionData:
        """
        Get document labels for a section.

        Args:
            request: Request containing register_id and section_id

        Returns:
            DocumentLabelsForSectionData with list of document labels
        """
        payload = request.request_body.request_payload
        register_id = payload.register_id
        section_id = payload.section_id
        _logger.info(f"Getting document labels for register_id: {register_id}, section_id: {section_id}")
        g2p_register_service = G2PRegisterService.get_component()
        return await g2p_register_service.get_document_labels_for_section(register_id, section_id)

    async def get_section_documents(
        self,
        request: GetSectionDocumentsRequest
    ) -> SectionDocumentsData:
        """
        Get documents for a section record.

        Args:
            request: Request containing register_id, record_id, and section_id

        Returns:
            SectionDocumentsData with list of documents (label, document_store_id)
        """
        payload = request.request_body.request_payload
        register_id = payload.register_id
        record_id = payload.record_id
        section_id = payload.section_id
        _logger.info(f"Getting section documents for register_id: {register_id}, record_id: {record_id}, section_id: {section_id}")
        g2p_register_service = G2PRegisterService.get_component()
        return await g2p_register_service.get_section_documents(register_id, record_id, section_id)

    async def get_section_documents_for_change_request(
        self,
        request: GetSectionDocumentsForChangeRequestRequest
    ) -> ChangeRequestDocumentsData:
        """
        Get documents for a change request.

        Args:
            request: Request containing change_request_id

        Returns:
            ChangeRequestDocumentsData with list of documents (label, document_store_id)
        """
        payload = request.request_body.request_payload
        change_request_id = payload.change_request_id
        _logger.info(f"Getting documents for change_request_id: {change_request_id}")
        g2p_register_service = G2PRegisterService.get_component()
        return await g2p_register_service.get_section_documents_for_change_request(change_request_id)

    async def get_file_url(
        self,
        request: FileUrlRequest
    ) -> FileUrlData:
        """
        Get the URL for a file.

        Args:
            request: Request containing file_name and bucket_name

        Returns:
            FileUrlData with URL for the specified file
        """
        payload = request.request_body.request_payload
        _logger.info(f"Getting file URL for file_name: {payload.file_name}, bucket_name: {payload.bucket_name}")

        minio_client = MinioClient.get_component()
        file_url = minio_client.get_url(payload.file_name, payload.bucket_name)
        return FileUrlData(file_url=file_url)
