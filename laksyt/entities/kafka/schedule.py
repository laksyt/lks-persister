from collections import namedtuple

from laksyt.config.config import Config

Schedule = namedtuple('Schedule', ['delay', 'timeout', 'max_records'])


def get_schedule(config: Config) -> Schedule:
    try:
        unparsed = config['kafka']['schedule']
    except KeyError:
        raise RuntimeError(
            "Missing key 'kafka.schedule'"
            f" in config file {config.profile.get_file_name()}"
        )
    if not unparsed:
        raise RuntimeError(
            "Empty key 'kafka.schedule'"
            f" in config file {config.profile.get_file_name()}"
        )
    field_names = "'%s'" % "', '".join(field for field in Schedule._fields)
    error_msg = "Key 'kafka.schedule'" \
                f" does not have all required fields ({field_names})" \
                f" in config file {config.profile.get_file_name()}"
    if not isinstance(unparsed, dict):
        raise RuntimeError(error_msg)
    try:
        schedule = Schedule(**unparsed)
    except (ValueError, TypeError):
        raise RuntimeError(error_msg)
    if not isinstance(schedule.delay, int) or not 5 <= schedule.delay <= 3600:
        raise RuntimeError(
            "Key 'kafka.schedule.delay' must be an int in range [5, 3600]"
            f" in config file {config.profile.get_file_name()}"
        )
    if not isinstance(schedule.timeout, int) or not 0 < schedule.timeout <= 20:
        raise RuntimeError(
            "Key 'kafka.schedule.timeout' must be an int in range (0, 20]"
            f" in config file {config.profile.get_file_name()}"
        )
    if not isinstance(schedule.max_records, int) \
            or not 0 < schedule.max_records <= 100:
        raise RuntimeError(
            "Key 'kafka.schedule.max_records' must be an int in range (0, 100]"
            f" in config file {config.profile.get_file_name()}"
        )
    return schedule
