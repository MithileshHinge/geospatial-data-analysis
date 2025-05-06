# Geo‑Data Visualization App – Database & Cache Design

## 0. Purpose of this document

This note explains **exactly** how to set up the PostgreSQL + PostGIS database (and companion Redis cache) that powers four API endpoints:

- `/v1/tiles/{layer}/{z}/{x}/{y}.{format}` – serve vector or GeoJSON map tiles
- `/v1/places/nearby` – find towns/cities near a point
- `/v1/reverse` – identify the county + MSA for a point
- `/v1/quickfacts/{layer}/{geoid}` – fetch Census QuickFacts for a region

The database is _read‑only_ after the initial load, so all guidance assumes immutable geometry.

---

## 1. Core concepts in PostGIS (fast primer)

- **SRID 4326** Standard lat/lon coordinates (WGS‑84). Every geometry in this project uses it.
- **`geometry` vs `geography`**

  - `geometry` stores raw lon/lat; distances come out in **degrees** unless you re‑project or cast.
  - `geography` stores curved‑earth coordinates; functions like `ST_Distance` return **metres** automatically.
  - We keep layer polygons as `geometry` (best for bounding‑box tile queries) but allow an extra _functional_ index to speed point‑radius searches (details later).

- **`GIST` index** Postgres tree index for spatial columns; accelerates `ST_Contains`, `ST_DWithin`, `&&` (bbox) and friends.
- **JSONB** Binary JSON. One column can hold an entire QuickFacts record. It supports indexing and partial fetches but we’ll mostly do key look‑ups.

---

## 2. Schema definition (DDL with commentary)

### 2.1 States – polygons

```sql
CREATE TABLE states (
    statefp  CHAR(2)  PRIMARY KEY,          -- 2‑digit state FIPS
    name     TEXT,
    geom     geometry(MULTIPOLYGON, 4326),  -- outline
    centroid geometry(POINT, 4326)
        GENERATED ALWAYS AS (ST_PointOnSurface(geom)) STORED
);
CREATE INDEX states_geom_gix ON states USING GIST (geom);
```

_`centroid` is auto‑filled; no extra code needed later._

### 2.2 Counties – polygons

```sql
CREATE TABLE counties (
    geoid    CHAR(5) PRIMARY KEY,           -- 5‑digit county FIPS
    statefp  CHAR(2) REFERENCES states,
    name     TEXT,
    geom     geometry(MULTIPOLYGON, 4326),
    centroid geometry(POINT, 4326)
        GENERATED ALWAYS AS (ST_PointOnSurface(geom)) STORED
);
CREATE INDEX counties_geom_gix ON counties USING GIST (geom);
```

### 2.3 MSAs (Metropolitan Statistical Areas) – polygons

```sql
CREATE TABLE msas (
    cbsa     CHAR(5) PRIMARY KEY,           -- 5‑digit CBSA code
    name     TEXT,
    geom     geometry(MULTIPOLYGON, 4326),
    centroid geometry(POINT, 4326)
        GENERATED ALWAYS AS (ST_PointOnSurface(geom)) STORED
);
CREATE INDEX msas_geom_gix ON msas USING GIST (geom);
```

### 2.4 Places – points (cities & towns)

```sql
CREATE TABLE places (
    geoid      CHAR(7) PRIMARY KEY,         -- 7‑digit place FIPS
    name       TEXT,
    pop        INTEGER,
    geom       geometry(POINT, 4326),       -- location
    county_id  CHAR(5) REFERENCES counties,
    msa_id     CHAR(5) REFERENCES msas
);
-- spatial index for bbox & contains
CREATE INDEX places_geom_gix    ON places USING GIST (geom);
-- population filter/sort helper
CREATE INDEX places_pop_btree   ON places (pop DESC);
-- optional: geography index to avoid casts in distance queries
CREATE INDEX places_geog_func_gix ON places USING GIST ((geom::geography));
```

`places_geog_func_gix` lets `ST_DWithin(geom::geography, …)` run without scanning the table.

### 2.5 QuickFacts – one JSONB blob per region

```sql
CREATE TABLE quickfacts (
    layer   TEXT   NOT NULL,               -- 'states' | 'counties' | 'places'
    geoid   TEXT   NOT NULL,
    facts   JSONB  NOT NULL,               -- entire Census fact record
    updated DATE   NOT NULL,
    PRIMARY KEY (layer, geoid)
);
CREATE INDEX quickfacts_layer_geoid ON quickfacts(layer, geoid);
```

Because `(layer, geoid)` is the primary key, `/quickfacts/{layer}/{geoid}` resolves in a single index lookup.

---

## 3. Index strategy & why it matters

- **Tile serving** uses the `geom && ST_TileEnvelope()` bbox predicate → hits the layer’s `GIST` geometry index (lightning fast).
- **Nearby search** casts points to geography and calls `ST_DWithin` → either uses the functional geography index or the geometry index followed by a fast cast.
- **Reverse geocode** (`ST_Contains`) also uses each layer’s `GIST` geometry index.

No manual tuning required beyond the indexes declared.

---

## 4. API → SQL quick‑reference

### 4.1 Tiles

```sql
SELECT ST_AsMVT(row, 'layer', 4096, 'geom')
FROM (
  SELECT geoid, name, geom
  FROM   counties                    -- swap for {layer}
  WHERE  geom && ST_TileEnvelope($z,$x,$y)
) row;
```

Return `ST_AsGeoJSON` instead of `ST_AsMVT` if `.geojson` was requested.

### 4.2 Nearby places

```sql
WITH pt AS (
  SELECT ST_SetSRID(ST_MakePoint($lon,$lat),4326)::geography AS g
)
SELECT geoid, name, pop,
       ST_Distance(geom::geography, pt.g) / 1000 AS dist_km
FROM   places, pt
WHERE  pop >= COALESCE($min_pop,0)
  AND  ST_DWithin(geom::geography, pt.g, $radius_km*1000)
ORDER  BY dist_km
LIMIT  $limit;
```

### 4.3 Reverse geocode

```sql
WITH pt AS (
  SELECT ST_SetSRID(ST_MakePoint($lon,$lat),4326) AS g
)
SELECT (
  SELECT row_to_json(c)
  FROM   counties c, pt
  WHERE  ST_Contains(c.geom, pt.g)
  LIMIT  1
) AS county,
(
  SELECT row_to_json(m)
  FROM   msas m, pt
  WHERE  ST_Contains(m.geom, pt.g)
  LIMIT  1
) AS msa;
```

### 4.4 QuickFacts

```sql
SELECT facts
FROM   quickfacts
WHERE  layer = $1   -- 'counties'
  AND  geoid = $2;  -- '06075'
```

---

## 5. Redis cache key plan (read‑through)

- **Tiles** `tile:{layer}:{z}:{x}:{y}:{fmt}` TTL 7 days
- **Nearby** `nearby:{lat4}:{lon4}:{radius}:{min_pop}:{limit}` TTL 1 hour
- **Reverse** `rev:{lat4}:{lon4}:{layers}` TTL 24 hours
- **QuickFacts** `qf:{layer}:{geoid}` TTL 24 hours

_`lat4`/`lon4` = coordinates rounded to 4 decimal places (\~10 m)._

---

## 6. ETL pipeline (one‑time + nightly refresher)

1. **Load TIGER geometries** with `shp2pgsql -I -s 4326` → each layer table.
2. **QuickFacts CSV → JSONB**: convert each row to JSON, then `COPY` into `quickfacts`.
3. **Let Postgres compute centroids** automatically (generated columns).
4. **Nightly job** (if new Census data): reload `quickfacts`, then `DEL qf:*` and `DEL tile:*` in Redis so next request repopulates fresh data.
5. **Optional**: create simplified materialized views for low‑zoom county/state polygons to shrink tile responses.

---

## 7. Choosing geometry vs geography (places table)

- `geometry(POINT,4326)` + functional geography index gives the **best mix**: fast bbox queries for map tiles **and** fast radial filters.
- Switching the column type to `GEOGRAPHY(POINT,4326)` removes the cast in distance queries but slows bbox tile generation a bit. Acceptable if tile serving does not hit the `places` table (usually true).

Given we serve _tiles from polygons_ and _nearby searches from points_, the hybrid approach (geometry column + geography index) keeps every query path optimal.

---
