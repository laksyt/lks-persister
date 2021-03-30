import psycopg2
from psycopg2._psycopg import connection

from laksyt.config.config import Config


def get_db_conn(config: Config, handle_client_exc=True) -> connection:
    try:
        postgres_uri: str = config['postgres']['uri']
    except KeyError:
        raise RuntimeError(
            "Missing key 'postgres.uri'"
            f" in config file {config.profile.get_file_name()}"
        )
    if not postgres_uri:
        raise RuntimeError(
            "Empty key 'postgres.uri'"
            f" in config file {config.profile.get_file_name()}"
        )
    try:
        return psycopg2.connect(postgres_uri)
    except Exception:
        if handle_client_exc:
            raise RuntimeError(
                "Failed to construct psycopg2 DB connection"
                " from value in key 'postgres.uri'"
                f" in config file {config.profile.get_file_name()}"
            )
