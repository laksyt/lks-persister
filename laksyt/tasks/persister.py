import asyncio
import logging

from kafka import KafkaConsumer
from psycopg2 import extensions
from psycopg2._psycopg import Error, connection
from psycopg2.extras import execute_values

from laksyt.entities.kafka.schedule import Schedule
from laksyt.entities.report import HealthReport, SQL_INSERT_REPORTS
from laksyt.entities.target import SQL_INSERT_TARGETS

logger = logging.getLogger(__name__)


class ReportPersister:

    def __init__(
            self,
            schedule: Schedule,
            kafka_consumer: KafkaConsumer,
            db_conn: connection
    ):
        self._schedule = schedule
        self._kafka_consumer = kafka_consumer
        self._db_conn = db_conn

    async def report_continuously(self):
        try:
            while True:
                self._check()
                await asyncio.sleep(self._schedule.delay)
        finally:
            self._db_conn.close()

    def _check(self):
        raw_messages = self._poll()
        reports = []
        for partition, messages in raw_messages.items():
            for message in messages:
                report = HealthReport.deserialize(message.value)
                reports.append(report)
                logger.info(f"Received {report}")
        self._kafka_consumer.commit()
        if reports:
            logger.info(f"Received batch of {len(reports)} reports; persisting")
            self._do_persist(reports)
        else:
            logger.info(f"Received empty batch")

    def _poll(self):
        return self._kafka_consumer.poll(
            timeout_ms=self._schedule.timeout * 1000,
            max_records=self._schedule.max_records
        )

    def _do_persist(self, reports: list[HealthReport]) -> None:
        if not reports:
            return
        try:
            with self._db_conn:
                with self._db_conn.cursor() as cursor:
                    self._insert_targets(reports, cursor)
                    self._insert_reports(reports, cursor)
        except Error:
            logger.exception(
                "Failed to persist latest batch of reports"
                ", they will be dropped"
            )

    @staticmethod
    def _insert_targets(
            reports: list[HealthReport],
            cursor: extensions.cursor
    ):
        return execute_values(
            cur=cursor,
            sql=SQL_INSERT_TARGETS,
            argslist=[
                (target.url, target.needle)
                for target in
                [report.target for report in reports]
            ]
        )

    @staticmethod
    def _insert_reports(
            reports: list[HealthReport],
            cursor: extensions.cursor
    ):
        return execute_values(
            cur=cursor,
            sql=SQL_INSERT_REPORTS,
            argslist=[
                (
                    report.target.url, report.target.needle,
                    report.is_available, report.status,
                    report.status_code, report.response_time,
                    report.needle_found, report.checked_at
                )
                for report in reports
            ]
        )
