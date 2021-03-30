-- Whether these commands are executed on application startup is controlled
-- from the app-<profile>.yml files

DROP TABLE IF EXISTS target, report CASCADE;
DROP VIEW IF EXISTS full_report CASCADE;
