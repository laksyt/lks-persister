import asyncio
import logging
from asyncio import Future
from typing import Optional

from persister.config.config import Config
from persister.logging import configure_logging
from persister.tasks.uptime import UptimeReporter


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
        self.task: Optional[Future] = None

        self.uptime_reporter = UptimeReporter()

    def launch(self):
        self.task = self.loop.create_task(self._workload())
        try:
            self.loop.run_forever()
        except asyncio.CancelledError:
            self.logger.warning("Cancelling event loop")
        except KeyboardInterrupt:
            self.logger.warning("Interrupting event loop")

    async def _workload(self):
        await asyncio.gather(
            self.uptime_reporter.report_continuously()
        )
