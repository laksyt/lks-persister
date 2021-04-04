import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from laksyt.config.config import Config
from laksyt.entities.kafka.consumer import get_kafka_consumer
from laksyt.entities.kafka.schedule import Schedule, get_schedule
from laksyt.entities.report import HealthReport

logger = logging.getLogger(__name__)


@dataclass
class KafkaMessage:
    """Represents the offset&bytes pair that is Kafka message"""
    offset: int
    raw_bytes: bytes


class KafkaPoller:
    """Wrapper around KafkaConsumer that continuously polls for messages and
    reports any errors along the way without breaking its stride
    """

    def __init__(
            self,
            schedule: Schedule,
            kafka_consumer: KafkaConsumer
    ):
        """Uses polling schedule and KafkaConsumer"""
        self._schedule = schedule
        self._kafka_consumer = kafka_consumer

    async def poll_continuously(self):
        """Exposes continuous polling function as an asynchronous generator"""
        while True:
            yield self._poll_once()
            await asyncio.sleep(self._schedule.delay)

    def _poll_once(self) -> Optional[list[HealthReport]]:
        """Does one synchronous poll and deserializes polled messages, if any,
        into HealthReports
        """
        batch = self._do_poll()
        return self._deserialize_batch(batch)

    def _do_poll(self) -> Optional[list[KafkaMessage]]:
        """Polls next limited batch of reports from Kafka, with timeout, then
        commits offsets and returns flat list of Kafka messages

        If polling or parsing fails, None is returned. For empty batches, an
        empty list is returned.
        """
        try:
            raw_messages = self._kafka_consumer.poll(
                timeout_ms=self._schedule.timeout * 1000,
                max_records=self._schedule.max_records
            )
        except KafkaError:
            logger.exception("Failed to poll for messages due to Kafka error")
            return None
        try:
            self._kafka_consumer.commit()
        except KafkaError:
            logger.exception("Failed to commit topic offset due to Kafka error")
        return self._parse_messages(raw_messages)

    @staticmethod
    def _parse_messages(raw_messages: Optional[dict]) \
            -> Optional[list[KafkaMessage]]:
        """Extracts flat list of Kafka messages from Kafka's output

        If given raw data cannot be parsed, an error is logged, then None is
        returned. If a batch has no messages, an empty list is returned.
        """
        result = None
        try:
            result = [
                KafkaMessage(message.offset, message.value)
                for _, messages in raw_messages.items()
                for message in messages
            ]
        except AttributeError:
            logger.exception(
                f"Failed to parse Kafka messages; dropping: {raw_messages}"
            )
        return result

    def _deserialize_batch(self, batch: Optional[list[KafkaMessage]]) \
            -> Optional[list[HealthReport]]:
        """Deserializes Kafka offset/message pairs and reports batch status"""
        if batch is None:
            return None  # polling errors reported where encountered
        reports = []
        if not batch:
            logger.info("Received empty batch of reports")  # valid case
            return reports
        for message in batch:
            report = self._deserialize_report(message)
            if report is not None:
                reports.append(report)
                logger.info(f"Received {report}")
        if not reports:
            logger.error(
                f"Failed to deserialize any of {len(batch)} Kafka messages"
                " in latest batch"
            )
        elif len(reports) != len(batch):
            logger.error(
                f"Failed to deserialize {len(batch) - len(reports)}"
                f" out of {len(batch)} Kafka messages in latest batch"
            )
        else:
            logger.info(f"Received batch of {len(reports)} reports")
        return reports

    @staticmethod
    def _deserialize_report(message: KafkaMessage) -> Optional[HealthReport]:
        """Deserializes Kafka message to HealthReport"""
        offset, raw_bytes = message.offset, message.raw_bytes
        report = None
        try:
            report = HealthReport.deserialize(raw_bytes)
        except StopIteration:  # deserialization fails with this exception
            logger.error(  # stack trace is more or less useless, so just error
                f"Failed to deserialize Kafka message [offset: {offset},"
                f" bytes: {raw_bytes}]; dropping"
            )
        return report


def get_kafka_poller(config: Config) -> KafkaPoller:
    """Extracts and validates Kafka consumer parameters from the application
    config file for the active profile, then constructs and returns the
    poller object
    """
    return KafkaPoller(
        get_schedule(config),
        get_kafka_consumer(config)
    )
