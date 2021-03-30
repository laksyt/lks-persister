import asyncio
import logging
import os
from os.path import join

from kafka import KafkaConsumer
from psycopg2 import extensions
from psycopg2._psycopg import Error, connection
from psycopg2.extras import execute_values

from laksyt.entities.kafka.schedule import Schedule
from laksyt.entities.report import HealthReport, SQL_INSERT_REPORTS
from laksyt.entities.target import SQL_INSERT_TARGETS

logger = logging.getLogger(__name__)
PROJECT_ROOT_DIR = join(os.path.dirname(__file__), os.pardir, os.pardir)
POSTGRES_INIT_SCHEMA_SQL_PATH = join(PROJECT_ROOT_DIR, 'sql', 'init_schema.sql')
POSTGRES_WIPE_SCHEMA_SQL_PATH = join(PROJECT_ROOT_DIR, 'sql', 'wipe_schema.sql')


class ReportPersister:
    """Main asynchronous workload

    Periodically polls Kafka topic for health check reports, then persists
    whatever messages were polled into configured PostgreSQL database
    """

    def __init__(
            self,
            schedule: Schedule,
            kafka_consumer: KafkaConsumer,
            db_conn: connection,
            init_schema_sql_path: str = POSTGRES_INIT_SCHEMA_SQL_PATH,
            wipe_schema_sql_path: str = POSTGRES_WIPE_SCHEMA_SQL_PATH
    ):
        """Accepts configuration, then, according to configuration preferences,
        executes startup SQL files on PostgreSQL instance
        """
        self._schedule = schedule
        self._kafka_consumer = kafka_consumer
        self._db_conn = db_conn
        if schedule.wipe_schema:
            self._exec_file(wipe_schema_sql_path)
        if schedule.wipe_schema or schedule.init_schema:
            self._exec_file(init_schema_sql_path)

    async def poll_continuously(self):
        """Repeatedly (with delay) performs rounds of Kafka polls"""
        try:
            while True:
                self.poll_once()
                await asyncio.sleep(self._schedule.delay)
        finally:
            self._db_conn.close()

    def poll_once(self):
        """Performs single Kafka poll and persists received health reports"""
        raw_messages = self._do_poll()
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

    def _do_poll(self) -> dict:
        """Polls next limited batch of reports from Kafka, with timeout"""
        return self._kafka_consumer.poll(
            timeout_ms=self._schedule.timeout * 1000,
            max_records=self._schedule.max_records
        )

    def _do_persist(self, reports: list[HealthReport]) -> None:
        """Persists given batch of health reports to PostgreSQL instance"""
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

    def _exec_file(self, sql_path: str) -> None:
        """Executes SQL file at given path against PostgreSQL instance"""
        try:
            with self._db_conn:
                with self._db_conn.cursor() as cursor:
                    cursor.execute(open(sql_path, 'r').read())
        except Error:
            self._db_conn.close()
            raise RuntimeError(
                f"Failed to execute SQL file at {sql_path}"
                " on PostgreSQL instance"
            )

    @staticmethod
    def _insert_targets(
            reports: list[HealthReport],
            cursor: extensions.cursor
    ):
        """Inserts given health check targets into relevant database table"""
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
        """Inserts given health check reports into relevant database table"""
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
