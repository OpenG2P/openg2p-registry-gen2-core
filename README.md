# openg2p-registry-gen2
Registry - Gen 2



# Ingestion Pipeline

- Create Partner API
    - Create API endpoints for ingestion
        - IngestData
            - Iterate through IncomingModelSignaturePatterns and decipher the partner and model details
            - Validate Signature
            - Insert data into IncomingRawData and IncomingRawDataPayload

- Beat Service

    # Service 1
    - Pickup PENDING from IncomingRawData
    - Emit ingest_id into Worker

    # Service 2
    - Pickup PENDING from IncomingClassifiedData
    

- Worker Service

    # For Service 1
    - Receive ingest_id
    - Fetch IncomingRawData and IncomingRawDataPayload for the ingest_id
    - Iterate through IncomingModelSemanticPatterns for that data_model and determine incoming register_id and opertion_id for that data_model_id
    - See if there is a record in IncomingPayloadEnricher for that data_model_id, register_id and operation_id
        - If yes, use that to enrich the payload and persist into IncomingEnrichedDataPayload
        - If no, use the raw payload as is
    - Persist into IncomingClassifiedData and update the IncomingRawData as PROCESSED

    # For Service 2
    - Receive ingest_id
    - Pickup Template from IncomingTemplate for the data_model, for register and operation
    - Process the template to get OpenG2P format/schema
    - Call Changelog Controller Service to persist data into OpenG2P