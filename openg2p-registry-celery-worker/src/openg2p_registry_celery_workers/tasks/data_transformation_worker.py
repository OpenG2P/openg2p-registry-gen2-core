import logging
from typing import Dict, Optional
from jinja2 import Template

from openg2p_registry_core.helpers.minio_client import MinioClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker
from openg2p_registry_core.models import (
    ProcessStatusEnum,
    IncomingTemplate,
    IncomingClassifiedData,
    IncomingRawDataPayload,
    IncomingPayloadEnricher,
    IncomingEnrichedTransformedData
)
from openg2p_registry_core.helpers import TemplateHelper
from openg2p_registry_extensions.ingestion_pipeline.factory.g2p_payload_enricher_factory import G2PPayloadEnricherFactory

from ..app import celery_app
from ..config import Settings
from ..engine import Engine

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = Engine.get_engine()


@celery_app.task(name="data_transformation_worker")
def data_transformation_worker(ingest_id: str):
    _logger.info(f"Starting data_transformation_worker for ingest_id: {ingest_id}")
    session_maker = sessionmaker(
        bind=_engine, expire_on_commit=False
    )

    with session_maker() as session:
        incoming_classified_data: IncomingClassifiedData = None
        try:
            incoming_classified_data = session.get(IncomingClassifiedData, ingest_id)
            incoming_raw_data_payload = session.get(IncomingRawDataPayload, ingest_id)
            
            incoming_enriched_transformed_data = IncomingEnrichedTransformedData(
                ingest_id=incoming_classified_data.ingest_id,
            )
            
            enriched_data_json: Dict = _enrich_raw_data_json(
                incoming_classified_data,
                incoming_raw_data_payload,
                session
            )
            incoming_enriched_transformed_data.enriched_data_json = enriched_data_json

            transformed_data_json: Dict = _transform_enriched_data_json(
                incoming_classified_data,
                enriched_data_json,
                session
            )
            incoming_enriched_transformed_data.transformed_data_json = transformed_data_json

            session.add(incoming_enriched_transformed_data)

            # Update incoming_classified_data transformation_status -> PROCESSED
            incoming_classified_data.transformation_status = ProcessStatusEnum.PROCESSED.value
            incoming_classified_data.transformation_date_time = func.now()

            # Update incoming_classified_data ingestion_status -> PENDING
            incoming_classified_data.ingestion_status = ProcessStatusEnum.PENDING.value
            session.commit()

        except Exception as e:
            _logger.error(
                f"Error during processing data_transformation_worker for ingest_id {ingest_id}: {str(e)}"
            )
            # Rollback all sessions
            session.rollback()

            # Update incoming_classified_data transformation_status -> FAILED
            incoming_classified_data.transformation_status = ProcessStatusEnum.FAILED.value
            incoming_classified_data.transformation_date_time = func.now()
            session.commit()
            # Raise exception for testing
            raise e

        _logger.info(
            f"Completed processing data_transformation_worker for ingest_id: {ingest_id}"
        )


def _enrich_raw_data_json(
    incoming_classified_data: IncomingClassifiedData, 
    incoming_raw_data_payload: IncomingRawDataPayload,
    session: Session
) -> Dict:
    incoming_payload_enricher: IncomingPayloadEnricher | None = session.execute(
        select(IncomingPayloadEnricher).filter_by(
            data_model_id=incoming_classified_data.data_model_id,
            register_id=incoming_classified_data.register_id,
            operation_id=incoming_classified_data.operation_id
        )
    ).scalar_one_or_none()

    enriched_data_json = None
    # Enrich and store in IncomingEnrichedTransformedData as enriched_data_json or enriched_data_xml
    if incoming_payload_enricher:
        raw_payload_enricher_class: str = incoming_payload_enricher.raw_payload_enricher_class
        g2p_payload_enricher_service = G2PPayloadEnricherFactory().get_enricher_service(raw_payload_enricher_class)
        enriched_data_json = g2p_payload_enricher_service.enrich(incoming_raw_data_payload.raw_data_json)
    else:
        enriched_data_json = incoming_raw_data_payload.raw_data_json
    
    enriched_data_json = enriched_data_json.get("body", enriched_data_json)
    return enriched_data_json

def _transform_enriched_data_json(
    incoming_classified_data: IncomingClassifiedData,
    enriched_data_json: Dict,
    session: Session
) -> Dict:
    incoming_template: IncomingTemplate | None = session.execute(
        select(IncomingTemplate).filter_by(
            data_model_id=incoming_classified_data.data_model_id,
            register_id=incoming_classified_data.register_id,
            operation_id=incoming_classified_data.operation_id
        )
    ).scalar_one_or_none()
    if not incoming_template:
        raise Exception(
            f"Template not found data_model_id {incoming_classified_data.data_model_id}, register_id {incoming_classified_data.register_id} and operation_id {incoming_classified_data.operation_id} combination"
        )
    
    minio_client = MinioClient.get_component()
    template_helper = TemplateHelper().get_component()

    transformed_data_json: Dict = template_helper.render_with_template(
        minio_client=minio_client,
        template_file_id=incoming_template.template_file_id,
        data=enriched_data_json
    )
    return transformed_data_json
