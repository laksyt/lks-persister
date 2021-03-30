-- On startup, application runs this SQL against the configured PostgreSQL
-- instance. Pre-existing tables are dropped before each run, to start from a
-- clean slate.

DROP TABLE IF EXISTS target, report CASCADE;
DROP VIEW IF EXISTS full_report CASCADE;

CREATE TABLE IF NOT EXISTS target (
    target_id serial,
    url text NOT NULL,
    needle text DEFAULT NULL,
    PRIMARY KEY (target_id),
    CONSTRAINT uq_url_needle UNIQUE (url, needle)
);

CREATE UNIQUE INDEX url_nullneedle_idx
    ON target (url) WHERE needle IS NULL;

CREATE TABLE IF NOT EXISTS report (
    report_id bigserial,
    target_id integer,
    is_available boolean NOT NULL,
    status varchar(16) NOT NULL,
    status_code smallint DEFAULT NULL,
    response_time double precision DEFAULT NULL,
    needle_found boolean DEFAULT NULL,
    checked_at timestamp with time zone NOT NULL,
    PRIMARY KEY (report_id),
    CONSTRAINT fk_target
      FOREIGN KEY (target_id)
          REFERENCES target (target_id)
          ON DELETE CASCADE
);

CREATE OR REPLACE VIEW full_report AS
SELECT t.url
     , r.is_available
     , r.status
     , r.status_code
     , r.response_time
     , t.needle
     , r.needle_found
     , r.checked_at
FROM target t JOIN report r USING (target_id);
