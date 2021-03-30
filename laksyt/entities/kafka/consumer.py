"""Extracts and validates Kafka consumer parameters from the application config
file for the active profile, then constructs and returns the consumer object
"""

from kafka import KafkaConsumer

from laksyt.config.config import Config


def get_kafka_consumer(config: Config) -> KafkaConsumer:
    kafka_consumer_config = config.extract_config_value(
        ('kafka', 'consumer'),
        lambda x: x is not None and isinstance(x, dict),
        lambda x: x,
        "dict with fields for KafkaConsumer constructor"
    )
    kafka_topic = config.extract_config_value(
        ('kafka', 'topic'),
        lambda x: x is not None and isinstance(x, str),
        lambda x: x,
        "str"
    )
    try:
        return KafkaConsumer(kafka_topic, **kafka_consumer_config)
    except Exception:
        raise RuntimeError(
            "Failed to construct KafkaConsumer from value(s)"
            f" at key 'kafka.consumer'"
            f" in config file {config.profile.get_file_name()}"
            f" (must be dict with fields for KafkaConsumer constructor)"
        )
