import asyncio
import logging
from asyncio import Future
from typing import Optional

from laksyt.config.config import Config
from laksyt.entities.kafka.consumer import get_kafka_consumer
from laksyt.entities.kafka.schedule import get_schedule
from laksyt.entities.postgres.dbconn import get_db_conn
from laksyt.logging import configure_logging
from laksyt.tasks.persister import ReportPersister
from laksyt.tasks.uptime import UptimeReporter


class Application:
    """Main entrypoint into the application

    Performs config duties, bootstraps the application, and exposes methods to
    launch the main process.
    """

    def __init__(self, config: Config):
        configure_logging(config)
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.loop = asyncio.get_event_loop()

        self.uptime_reporter = UptimeReporter()
        self.report_persister = ReportPersister(
            get_schedule(config),
            get_kafka_consumer(config),
            get_db_conn(config)
        )

    def launch(self):
        self.loop.create_task(self._workload())
        try:
            self.loop.run_forever()
        except asyncio.CancelledError:
            self.logger.warning("Cancelling event loop")
        except KeyboardInterrupt:
            self.logger.warning("Interrupting event loop")

    async def _workload(self):
        await asyncio.gather(
            self.uptime_reporter.report_continuously(),
            self.report_persister.report_continuously()
        )
