from laksyt.config.config import Config
from laksyt.config.profiles import Profiles
from laksyt.entities.kafka.startup import Startup, get_startup
from tests.utilities import create_default_profile_config_file


class TestStartup:

    def test_get_startup(self, tmpdir):
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
        startup: Startup = get_startup(Config(Profiles(profile_dir=tmpdir)))

        # Then
        assert startup.init_schema is True
        assert startup.wipe_schema is False
