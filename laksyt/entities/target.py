from dataclasses import dataclass
from typing import Optional

from dataclasses_avroschema import AvroModel

SQL_INSERT_TARGETS = "INSERT INTO target ( url, needle ) " \
                     "VALUES %s ON CONFLICT DO NOTHING;"


@dataclass
class Target(AvroModel):
    url: str
    needle: Optional[str] = None
