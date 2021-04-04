import logging
import os
from os.path import join
from typing import Optional

from psycopg2 import extensions
from psycopg2._psycopg import Error, connection
from psycopg2.extras import execute_values

from laksyt.entities.kafka.poller import KafkaPoller
from laksyt.entities.kafka.startup import Startup
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
            startup: Startup,
            kafka_poller: KafkaPoller,
            db_conn: connection,
            init_schema_sql_path: str = POSTGRES_INIT_SCHEMA_SQL_PATH,
            wipe_schema_sql_path: str = POSTGRES_WIPE_SCHEMA_SQL_PATH
    ):
        """Accepts configuration, then, according to configuration preferences,
        executes startup SQL files on PostgreSQL instance
        """
        self._kafka_poller = kafka_poller
        self._db_conn = db_conn
        if startup.wipe_schema:
            self._exec_file(wipe_schema_sql_path)
        if startup.wipe_schema or startup.init_schema:
            self._exec_file(init_schema_sql_path)

    async def persist_continuously(self):
        """Consumes KafkaPoller as an asynchronous generator and persists
        received report batches
        """
        try:
            async for batch in self._kafka_poller:
                self._persist_once(batch)
        finally:
            self._db_conn.close()

    def _persist_once(self, batch: Optional[list[HealthReport]]) -> None:
        """Persists single batch of health reports"""
        if not batch:
            return  # all polling errors logged where encountered
        else:
            logger.info(f"Persisting batch of {len(batch)} reports")
            self._do_persist(batch)

    def _do_persist(self, batch: list[HealthReport]) -> None:
        """Persists given batch of health reports to PostgreSQL instance"""
        try:
            with self._db_conn:
                with self._db_conn.cursor() as cursor:
                    self._insert_targets(batch, cursor)
                    self._insert_reports(batch, cursor)
        except Error:
            logger.exception(
                "Failed to persist latest batch of reports; dropping"
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

    def _exec_file(self, sql_path: str) -> None:
        """Executes SQL file at given path against PostgreSQL instance"""
        logger.info(f"Executing SQL script at {sql_path}")
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
