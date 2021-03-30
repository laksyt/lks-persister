from laksyt.config.config import Config
from laksyt.config.profiles import Profiles
from laksyt.entities.postgres.dbconn import get_db_conn
from tests.utilities import create_default_profile_config_file


class TestDBConn:

    def test_get_db_conn(self, tmpdir):
        # Given
        create_default_profile_config_file(
            tmpdir,
            '''
postgres:
  uri: postgres://user:pwd@non-existing-postgres-server.aivencloud.com:22222/database?sslmode=require
            '''
        )

        # When
        get_db_conn(
            Config(Profiles(config_dir=tmpdir)),
            handle_client_exc=False
        )

        # Then no config parsing errors are raised
