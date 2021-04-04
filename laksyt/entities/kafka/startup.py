"""Defines an abstraction for storing startup configuration

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

Startup = namedtuple(
    'Startup',
    [
        'init_schema',
        'wipe_schema'
    ]
)


def get_startup(config: Config) -> Startup:
    """Extracts and validates startup parameters from the application config
    file for the active profile
    """
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
    return Startup(
        init_schema=db_init_schema,
        wipe_schema=db_wipe_schema
    )
