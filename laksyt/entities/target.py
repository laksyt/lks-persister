"""Abstraction for health check target, to be reconstructed from Avro messages
polled from Kafka topic. SQL query template is defined here to be used for
persisting the instances in a PostgreSQL database.

url (str): URL to send a GET request to.
needle (str): Unparsed regex pattern to search for in the HTML content returned
    from the website.
"""

from dataclasses import dataclass
from typing import Optional

from dataclasses_avroschema import AvroModel

SQL_INSERT_TARGETS = "INSERT INTO target ( url, needle ) " \
                     "VALUES %s ON CONFLICT DO NOTHING;"


@dataclass
class Target(AvroModel):
    url: str
    needle: Optional[str] = None
