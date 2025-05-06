# Geo Data API – Endpoint & Contract Reference

## 0 · Scope & Guarantees

- **Read-only** – every call is idempotent; no data mutation.
- **Versioned paths** – all user-visible endpoints are under `/v1/…`. Future breaking changes bump the prefix.
- **Auth** – _none_ in dev; add a bearer header later (`Authorization: Bearer <jwt>`).
- **Formats** – JSON (`application/json`) unless otherwise noted; vector tiles are gzip-compressed MVT.
- **Rate‐limits** – 10 req/second, 600 req/min

---

## 1 · Glossary

| Term       | Meaning                                                          |     |     |     |
| ---------- | ---------------------------------------------------------------- | --- | --- | --- |
| **layer**  | \`"states", "counties", "msas", "places"\`                       |     |     |     |
| **geoid**  | State FIPS (2) · County FIPS (5) · MSA CBSA (5) · Place FIPS (7) |     |     |     |
| **format** | `"mvt"` (Mapbox vector-tile, default), `"geojson"`               |     |     |     |
| **units**  | Kilometres                                                       |     |     |     |

---

## 2 · Endpoint index

| Path                                     | Method | Purpose                     |
| ---------------------------------------- | ------ | --------------------------- |
| `/v1/tiles/{layer}/{z}/{x}/{y}.{format}` | `GET`  | Stream vector/GeoJSON tiles |
| `/v1/places/nearby`                      | `GET`  | Cities/towns within radius  |
| `/v1/reverse`                            | `GET`  | County & MSA at a point     |
| `/v1/quickfacts/{layer}/{geoid}`         | `GET`  | Census QuickFacts blob      |
| `/healthz`                               | `GET`  | Liveness probe (no auth)    |

---

## 3 · Detailed contract

### 3.1 Tiles

```
GET /v1/tiles/{layer}/{z}/{x}/{y}.{format}
```

| Param       | In   | Type   | Constraints        | Notes        |
| ----------- | ---- | ------ | ------------------ | ------------ |
| `layer`     | path | string | enum               | see glossary |
| `z` `x` `y` | path | int    | `0 ≤ z ≤ 22`       | Web-Mercator |
| `format`    | path | string | `mvt` \| `geojson` |              |

- **Success 200** –
  _`mvt`_: `Content-Type: application/vnd.mapbox-vector-tile` (gzip)
  _`geojson`_: `Content-Type: application/geo+json`
- **Errors** – `404` if tile empty, `422` on bad params.

**Cache key** `tile:{layer}:{z}:{x}:{y}:{format}` – TTL 7 days.

---

### 3.2 Nearby places

```
GET /v1/places/nearby
```

| Query       | Type  | Default | Constraints | Description    |
| ----------- | ----- | ------- | ----------- | -------------- |
| `lat`       | float | –       | −90 … 90    | WGS-84 dec-deg |
| `lon`       | float | –       | −180 … 180  |                |
| `radius_km` | int   | 50      | 1 … 500     | Search radius  |
| `limit`     | int   | 25      | 1 … 100     | Max rows       |

```jsonc
// 200 OK
{
  "results": [
    {
      "geoid": "0667000",
      "name": "San Francisco",
      "lat": 37.7749,
      "lon": -122.4194,
      "distance_km": 12.3
    },
    …
  ]
}
```

- `404` never returned (empty array is valid).

---

### 3.3 Reverse county & MSA lookup

```
GET /v1/reverse
```

| Query    | Type  | Default         | Description                         |
| -------- | ----- | --------------- | ----------------------------------- |
| `lat`    | float | –               | Point lat                           |
| `lon`    | float | –               | Point lon                           |
| `layers` | str   | `counties,msas` | Comma list; may include one or both |

```jsonc
// 200 OK
{
  "county": { "geoid": "06037", "name": "Los Angeles County, CA" },
  "msa": { "geoid": "31080", "name": "Los Angeles–Long Beach–Anaheim, CA MSA" }
}
```

- Keys absent if layer not requested.

---

### 3.4 QuickFacts

```
GET /v1/quickfacts/{layer}/{geoid}
```

- **Success 200** – returns _raw_ Census QuickFacts JSON object (tens of kB), around 70 data points like "Population estimates, July 1, 2024, (V2024)", "Owner-occupied housing unit rate, 2019-2023", etc
- **404** – if `(layer, geoid)` not found.

Cache key `qf:{layer}:{geoid}` – TTL 24 h.

---

### 3.5 Healthz

```
GET /healthz
```

_Runs `SELECT 1` against Postgres._
Returns `204 No Content` if process & DB are alive.

---

## 4 · Common error schema

```jsonc
// 4xx / 5xx
{
  "detail": "Human-readable explanation"
}
```

Status codes used:

| Code | When                                        |
| ---- | ------------------------------------------- |
| 400  | Malformed request body (future)             |
| 401  | Missing/expired auth token (future)         |
| 403  | Auth OK but not allowed (future)            |
| 404  | Resource not found, or empty tile           |
| 429  | Rate-limit exceeded                         |
| 422  | Parameter validation failed                 |
| 500  | Unhandled error (should not leak internals) |

---

## 5 · Example curl cheatsheet

```bash
# vector tile (gzipped MVT)
curl -o county.mvt \
  'https://api.example.com/v1/tiles/counties/6/10/25.mvt'

# nearby towns 40 km around Austin, TX
curl 'https://api.example.com/v1/places/nearby?lat=30.27&lon=-97.74&radius_km=40'

# reverse lookup (Atlanta downtown)
curl 'https://api.example.com/v1/reverse?lat=33.75&lon=-84.39'

# QuickFacts for California
curl 'https://api.example.com/v1/quickfacts/states/06' | jq
```

---

## 6 · Versioning & deprecation

1. **Minor fields** – additive; no path change, document in changelog.
2. **Breaking change** – introduce `/v2/…`, run dual for 6 months, then retire `/v1/`.
3. **EOL policy** – oldest version kept ≥ 12 months from first v2 GA release.

---

## 7 · Performance & cache notes for integrators

| Endpoint   | In-memory Redis TTL | Can be CDN-cached? | Hint header                                      |
| ---------- | ------------------- | ------------------ | ------------------------------------------------ |
| Tiles      | 7 days              | **Yes**            | `Cache-Control: public,max-age=604800,immutable` |
| Nearby     | 1 h                 | No                 | `Cache-Control: private,max-age=3600`            |
| Reverse    | 24 h                | No (coords vary)   | `Cache-Control: private,max-age=86400`           |
| QuickFacts | 24 h                | **Yes**            | `Cache-Control: public,max-age=86400`            |

Tiles & QuickFacts are immutable until the next TIGER/Census refresh.
