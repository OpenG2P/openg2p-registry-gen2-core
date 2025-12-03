BEAT and WORKER
	Periodically (1 hour or 1 day) — > Wake UP and the WORKER will call —> CRVS_REGISTRY / SEARCH — This will be hosted by OpenCRVS
	SEARCH CRITERIA —> ALL NEW BIRTHS in the LAST 1 Week
	We will get SEARCH RESPONSE — LIST<MEMBER>
SEARCH RESPONSE —> will have to send to INGEST_API — > data_model — query_param - spdci
BEAT_PRODUCER
g2p_crvs_birth_puller
WORKERS
g2p_crvs_birth_puller