from laksyt.config.config import Config
from laksyt.config.profiles import Profiles
from laksyt.entities.kafka.schedule import Schedule, get_schedule
from tests.utilities import create_default_profile_config_file


class TestSchedule:

    def test_get_schedule(self, tmpdir):
        # Given
        create_default_profile_config_file(
            tmpdir,
            '''
kafka:
  schedule:
    delay: 10
    timeout: 3
    max_records: 12
postgres:
  startup:
    init_schema: true
    wipe_schema: false
            '''
        )

        # When
        schedule: Schedule = get_schedule(Config(Profiles(profile_dir=tmpdir)))

        # Then
        assert schedule.delay == 10
        assert schedule.timeout == 3
        assert schedule.max_records == 12
