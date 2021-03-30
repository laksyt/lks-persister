from laksyt.config.config import Config
from laksyt.config.profiles import Profiles
from laksyt.entities.kafka.consumer import get_kafka_consumer
from tests.utilities import create_default_profile_config_file


class TestKafkaConsumer:

    def test_get_kafka_consumer(self, tmpdir):
        # Given
        create_default_profile_config_file(
            tmpdir,
            '''
kafka:
  consumer:
    bootstrap_servers: non-existing-kafka-server.aivencloud.com:22222
    auto_offset_reset: earliest
    client_id: lks-persister-1
    group_id: lks-persister-group
    security_protocol: SSL
    ssl_cafile: ca.pem
    ssl_certfile: service.cert
    ssl_keyfile: service.key
  topic: PLACEHOLDER
            '''
        )

        # When
        get_kafka_consumer(
            Config(Profiles(config_dir=tmpdir)),
            handle_kafka_exc=False
        )

        # Then no config parsing errors are raised
