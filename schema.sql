-- enable: postgis
CREATE EXTENSION IF NOT EXISTS postgis;

-- boundary
DROP TABLE IF EXISTS boundary;
CREATE TABLE  boundary (
    id serial PRIMARY KEY,
    data json,
    geom geometry(Geometry, 4326)
);
CREATE INDEX idx_boundary_geom ON boundary USING gist (geom);

-- poi
DROP TABLE IF EXISTS poi;
CREATE TABLE poi (
    id serial PRIMARY KEY,
    data json,
    lat float,
    lng float,
    geom geometry(Geometry, 4326)
);
CREATE INDEX idx_poi_geom ON poi USING gist (geom);