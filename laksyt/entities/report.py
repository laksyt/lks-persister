"""Abstraction for health check report, to be reconstructed from Avro messages
polled from Kafka topic. SQL query template is defined here to be used for
persisting the instances in a PostgreSQL database.

target (Target): Website to check and regex to search for.
is_available (bool): Whether a response was received.
status (str): Human-readable description of health check result.
status_code (int): HTTP response code (if it was received).
response_time (float): Number of seconds that request took.
needle_found (bool): Whether given regex matched anywhere in page HTML (if
    there was a response at all).
checked_at (datetime): Timestamp (in UTC) when health check was completed.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from dataclasses_avroschema import AvroModel

from laksyt.entities.target import Target

SQL_INSERT_REPORTS = """
INSERT INTO report ( target_id, is_available, status, status_code, response_time, needle_found, checked_at )
SELECT t.target_id::integer
    , r.is_available::boolean
    , r.status::varchar(16)
    , r.status_code::smallint
    , r.response_time::double precision 
    , r.needle_found::boolean
    , r.checked_at::timestamp with time zone
FROM target t
INNER JOIN ( VALUES %s ) r ( url, needle , is_available, status, status_code, response_time, needle_found, checked_at )
ON ((t.url = r.url AND t.needle = r.needle) OR (t.url = r.url AND t.needle IS NULL AND r.needle IS NULL));
"""


@dataclass
class HealthReport(AvroModel):
    target: Target
    is_available: bool
    status: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    needle_found: Optional[bool] = None
    checked_at: datetime = field(init=False)
