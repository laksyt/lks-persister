from kafka import KafkaConsumer

from laksyt.config.config import Config


def get_kafka_consumer(config: Config) -> KafkaConsumer:
    try:
        kafka_dict: dict = config['kafka']['consumer']
    except KeyError:
        raise RuntimeError(
            "Missing key 'kafka.consumer'"
            f" in config file {config.profile.get_file_name()}"
        )
    if not kafka_dict:
        raise RuntimeError(
            "Empty key 'kafka.consumer'"
            f" in config file {config.profile.get_file_name()}"
        )

    try:
        topic = config['kafka']['topic']
    except KeyError:
        raise RuntimeError(
            "Missing key 'kafka.topic'"
            f" in config file {config.profile.get_file_name()}"
        )
    if not isinstance(topic, str):
        raise RuntimeError(
            "Key 'kafka.topic' should be string"
            f" in config file {config.profile.get_file_name()}"
        )

    try:
        return KafkaConsumer(topic, **kafka_dict)
    except Exception:
        raise RuntimeError(
            "Failed to construct KafkaProducer"
            " from values in key 'kafka.consumer'"
            f" in config file {config.profile.get_file_name()}"
        )
