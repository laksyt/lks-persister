"""Defines an abstraction for storing scheduling configuration

delay (int): Duration in seconds between the end of a round of Kafka polling
    and the beginning of the next one.
timeout (int): Duration in seconds to wait for a response from Kafka before
    giving up (for current round).
max_records (int): Limit of messages to poll from Kafka per round.
init_schema (bool): Whether on application startup to create pre-existing
    tables and views that this application uses in the configured PostgreSQL
    instance, unless they already exist. If wipe_schema is True, then this is
    also True regardless of config value.
wipe_schema (bool): Whether on application startup to wipe and re-create
    pre-existing tables and views that this application uses in the configured
    PostgreSQL instance.
"""
import logging
from collections import namedtuple

from laksyt.config.config import Config

Schedule = namedtuple(
    'Schedule',
    [
        'delay',
        'timeout',
        'max_records',
        'init_schema',
        'wipe_schema'
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
        lambda x: x is not None and isinstance(x, int) and 0 < x <= 20,
        lambda x: x,
        'int in range (0,20]'
    )
    kafka_max_records = config.extract_config_value(
        ('kafka', 'schedule', 'max_records'),
        lambda x: x is not None and isinstance(x, int) and 0 < x <= 100,
        lambda x: x,
        'int in range (0, 100]'
    )
    db_init_schema = config.extract_config_value(
        ('postgres', 'startup', 'init_schema'),
        lambda x: x is not None and isinstance(x, bool),
        lambda x: x,
        'bool'
    )
    db_wipe_schema = config.extract_config_value(
        ('postgres', 'startup', 'wipe_schema'),
        lambda x: x is not None and isinstance(x, bool),
        lambda x: x,
        'bool'
    )
    if db_wipe_schema and not db_init_schema:
        logging.getLogger(__name__).warning(
            "Configuration is set to wipe database schema, but not"
            " re-initialize it afterward: despite configuration, schema will be"
            " re-initialized"
        )
        db_init_schema = True
    return Schedule(
        delay=kafka_delay,
        timeout=kafka_timeout,
        max_records=kafka_max_records,
        init_schema=db_init_schema,
        wipe_schema=db_wipe_schema
    )
