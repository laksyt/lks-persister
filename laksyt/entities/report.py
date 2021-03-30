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
