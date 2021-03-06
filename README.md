# Läksyt: Persister

<p align="center">
<em>‘Läksyt’ is plural for ‘homework’ in Finnish<br>(according to <a href="https://translate.google.com/?sl=fi&tl=en&text=l%C3%A4ksyt&op=translate">Google Translate</a>)</em>
</p>

A Python micro-service that periodically polls a Kafka topic for Avro messages, deserializes them into dataclass
instances (website health-check reports), then persists the received health reports to a PostgreSQL instance.

## Configure

All configuration resides in the file `profiles/app-default.yml`.

The application looks for the `profiles` directory in the caller’s current working directory, then, if not found, in the
application’s root directory (the one that contains `main.py`).

At the minimum, this application requires connection credentials to instances of Kafka and PostgreSQL, and also a Kafka
topic name to poll from. Other preferences are set to reasonable defaults and should prove intuitive to tinker with.

The application supports multiple configuration profiles: just add a file `profiles/app-<PROFILE_NAME>.yml` for each
additional profile.
(The profile `default` must always be present as it is, well, the default.)
To select the active profile:

* Set the environment variable `LAKSYT_PROFILE` to the value `<PROFILE_NAME>`.
* Or, add the command line option `--profile <PROFILE_NAME>`/`-p <PROFILE_NAME>` to the `python` command when launching
  the application.
* Otherwise, the `default` profile will be used.

The profile name given in the command line overrides the profile from the environment variable.

### Database schema

The SQL commands that initialize tables & views in the PostgreSQL instance are located in the `sql/` directory. By
default, the schema is created on application start-up, unless identically named tables already exist. It is possible to
wipe pre-existing tables & views on application start-up by setting `postgres.startup.wipe_schema` key to `true` in the
configuration file (e.g., `profiles/app-default.yml`).

## Run

### Run with `pipenv`

To run the application with `pipenv`, first install the dependencies:

```shell
pipenv install --deploy --ignore-pipfile
```

Then run the application:

```shell
pipenv run python main.py
```

To select a non-default profile, append `-p <PROFILE_NAME>` to the `pipenv run` command.

### Run with Docker

To run the application with Docker, first build the image:

```shell
docker build -t laksyt/lks-persister:latest .
```

Then run the application:

```shell
docker run -it --rm laksyt/lks-persister:latest
```

To select a non-default profile, append `-e LAKSYT_PROFILE=<PROFILE_NAME>` to the `docker run` options.

## While running

The application logs its normal activities into the standard error at the `INFO` level. The lowest outputted log level
is controlled by the configuration key `log.level`.

To stop the execution, just send a `Ctrl-C`.
