"""Defines an abstraction for storing scheduling configuration

delay (int): Duration in seconds between the end of a round of Kafka polling
    and the beginning of the next one.
timeout (int): Duration in seconds to wait for a response from Kafka before
    giving up (for current round).
max_records (int): Limit of messages to poll from Kafka per round.
"""

from collections import namedtuple

from laksyt.config.config import Config

Schedule = namedtuple(
    'Schedule',
    [
        'delay',
        'timeout',
        'max_records'
    ]
)


def get_schedule(config: Config) -> Schedule:
    """Extracts and validates scheduling parameters from the application config
    file for the active profile
    """
    kafka_delay = config.extract_config_value(
        ('kafka', 'schedule', 'delay'),
        lambda x: x is not None and isinstance(x, int) and 5 <= x <= 3600,
        lambda x: x,
        'int in range [5,3600]'
    )
    kafka_timeout = config.extract_config_value(
        ('kafka', 'schedule', 'timeout'),
        lambda x: x is not None and isinstance(x, int) and 0 < x <= 60,
        lambda x: x,
        'int in range (0,60]'
    )
    kafka_max_records = config.extract_config_value(
        ('kafka', 'schedule', 'max_records'),
        lambda x: x is not None and isinstance(x, int) and 0 < x <= 100,
        lambda x: x,
        'int in range (0, 100]'
    )
    return Schedule(
        delay=kafka_delay,
        timeout=kafka_timeout,
        max_records=kafka_max_records
    )
