CREATE SCHEMA bottletube;
SET SCHEMA 'bottletube';

CREATE TABLE IF NOT EXISTS image_uploads(
    id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    url VARCHAR(256) NOT NULL,
    category varchar(64)
);