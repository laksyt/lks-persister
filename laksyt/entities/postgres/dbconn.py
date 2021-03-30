"""Extracts and validates psycopg2 parameters from the application config
file for the active profile, then constructs and returns the client object
"""

import psycopg2
from psycopg2._psycopg import connection

from laksyt.config.config import Config


def get_db_conn(config: Config) -> connection:
    return config.extract_config_value(
        ('postgres', 'uri'),
        lambda x: x is not None and isinstance(x, str),
        lambda x: psycopg2.connect(x),
        "PostgreSQL instance connection URI"
    )
