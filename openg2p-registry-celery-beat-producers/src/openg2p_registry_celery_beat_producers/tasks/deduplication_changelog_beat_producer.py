import logging
from typing import List

from openg2p_registry_core.models import G2PRegisterChangeLog, DeduplicationStatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app
from ..config import Settings
from ..engine import Engine
from ..utils import Workers

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = Engine.get_engine()


@celery_app.task(name="deduplication_changelog_beat_producer")
def deduplication_changelog_beat_producer():
    """
    Beat producer that finds pending deduplication work for changelog records
    and queues them to the deduplication worker.
    """
    _logger.info("Checking for pending deduplication_changelog requests")
    session_maker = sessionmaker(bind=_engine, expire_on_commit=False)
    
    with session_maker() as session:
        # Fetch change logs with pending changelog deduplication status
        pending_changelogs: List[G2PRegisterChangeLog] = (
            session.execute(
                select(G2PRegisterChangeLog)
                .filter(
                    G2PRegisterChangeLog.deduplication_changelog_status
                    == DeduplicationStatusEnum.PENDING.value
                )
                .limit(_config.no_of_tasks_to_process)
            )
            .scalars()
            .all()
        )
        _logger.info(f"Found {len(pending_changelogs)} PENDING deduplication_changelog requests")

        for change_log in pending_changelogs:
            _logger.info(f"Queueing change_log {change_log.change_log_id} for changelog deduplication")

            # Update status to INPROGRESS
            change_log.deduplication_changelog_status = DeduplicationStatusEnum.INPROGRESS.value
            session.add(change_log)

            _logger.info(
                f"Updating status for {Workers.DEDUPLICATION_CHANGELOG_WORKER} to INPROGRESS for change_log: {change_log.change_log_id}"
            )

            # Send task to celery worker
            celery_app.send_task(
                Workers.DEDUPLICATION_CHANGELOG_WORKER,
                args=(change_log.change_log_id,),
                queue=_config.worker_queue,
            )
            _logger.info(
                f"Sent task to {Workers.DEDUPLICATION_CHANGELOG_WORKER} for change_log: {change_log.change_log_id}"
            )
        session.commit()

    _logger.info("Completed processing pending deduplication_changelog requests")

