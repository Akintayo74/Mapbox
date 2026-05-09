# Personal Cartography — Project Brief

A self-hosted, privacy-respecting personal location tracker and map viewer. Track movements via Android, store the data in your own database, and build a beautiful, custom map view to explore your own life.

---

## Vision

Build something like Google Timeline, but as a personal artifact — an instrument for looking at your own life, designed with intentionality and craft. The location tracking infrastructure is the ingest layer; the actual project is the **viewer** — what it shows, what it lets you ask, how it feels to open on a Sunday evening and scroll through last month.

The aesthetic target is in the lineage of the Mapbox homepage, Arc, Linear, and Notion: warm, considered, calm. Not a dashboard. Not a logistics tool. An instrument.

---

## Stack

| Layer | Choice | Reasoning |
|---|---|---|
| **Mobile client** | [Colota](https://colota.app/) (F-Droid build, no Google Play Services) | Client-only, no bundled server, sends to any HTTP endpoint, modern battery management (tracking profiles, stationary GPS pause), exports GeoJSON natively |
| **Frontend framework** | SvelteKit (JavaScript) | Cohesive full-stack framework, Svelte 5 runes are a strong reactivity model, fits a single-page interactive app better than Astro |
| **Map library** | Mapbox GL JS | Native heatmap layer, vector tile support, custom Studio styles, generous free tier (50k loads/month) |
| **Database** | Neon (managed Postgres + PostGIS) | Serverless, scale-to-zero, free tier, PostGIS available as an extension, fully exportable via `pg_dump` if migration is ever needed |
| **App hosting** | Fly.io (when needed) | Deploy SvelteKit when the phone needs to reach the API from outside the local network |
| **Tile pipeline** | [tippecanoe](https://github.com/felt/tippecanoe) — *deferred until needed* | Vector tile generation for large datasets. Not introduced until direct GeoJSON rendering becomes painful (somewhere past 100k points) |

### Stack decisions worth knowing the reasoning for

- **Colota over ulogger:** ulogger ships an opinionated PHP server with a viewer that we don't want. Colota is client-only and posts to any HTTP endpoint we define. This is exactly the right shape — Colota handles ingest, we own everything downstream.
- **Neon over self-hosted Postgres:** Self-hosting is valuable when it protects against fears we actually have. Neon protects against vendor lock-in (data is exportable Postgres), training-on-data (reputable provider), and shutdown (we can migrate in 15 minutes). The thing it doesn't protect against — vendor existing at all — is a real but smaller concern. Easy to migrate to a VPS later.
- **SvelteKit over Astro:** Astro is excellent for content-heavy sites with islands of interactivity. This app is the inverse — one big interactive surface. SvelteKit's cohesion as a full-stack framework fits better.
- **No tippecanoe yet:** Infrastructure for scale you don't have is the most expensive kind of infrastructure. Direct GeoJSON works fine for the foreseeable horizon. Introduce tiles when latency hurts, not before.

---

## Data shape

Points stored as flat rows. The shape mirrors what Colota sends and what the viewer consumes.

```jsonc
{
  "id": 1,
  "latitude": 9.943928,
  "longitude": 8.861903,
  "timestamp": "2026-04-13T06:00:00+01:00",  // ISO 8601 with WAT offset
  "accuracy": 10.0,                          // meters
  "speed": 7.78,                             // m/s (Colota convention)
  "bearing": 187.4,                          // degrees from north
  "altitude": 1200,                          // meters
  "battery": 80                              // percent
}
```

Conversion to GeoJSON happens in the viewer (or the API route), not at storage time. GeoJSON uses `[longitude, latitude]` ordering — easy to get backwards.

### Postgres schema (when ready)

```sql
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE points (
  id           BIGSERIAL PRIMARY KEY,
  latitude     DOUBLE PRECISION NOT NULL,
  longitude    DOUBLE PRECISION NOT NULL,
  geom         GEOGRAPHY(POINT, 4326) GENERATED ALWAYS AS
                 (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography) STORED,
  recorded_at  TIMESTAMPTZ NOT NULL,
  accuracy     REAL,
  speed        REAL,
  bearing      REAL,
  altitude     REAL,
  battery      SMALLINT,
  received_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX points_recorded_at_idx ON points (recorded_at DESC);
CREATE INDEX points_geom_idx ON points USING GIST (geom);
```

The generated `geom` column lets PostGIS do spatial queries (bounding box, distance, "within polygon") for free. The two indexes cover the two query patterns: time-range filters and spatial filters.

---

## Build phases

### Phase 1 — Viewer with fake data (now)
**Goal:** Discover what you want the viewer to be, before building anything that depends on the answer.

- SvelteKit project, single route renders a Mapbox GL JS map
- Load fake `points.geojson` from `static/`
- Render points as circles, paths as lines
- Iterate on style, interaction, layout
- No backend, no database

**Done when:** You can articulate clearly what the viewer should show and how it should feel. You'll know what columns the database needs because you'll know what the viewer queries.

### Phase 2 — Ingest endpoint + Neon
**Goal:** Get real data flowing.

- Neon project + database, run the schema above
- SvelteKit API route at `/api/track` that accepts Colota's POST payload, validates a bearer token, inserts into Postgres
- Deploy SvelteKit to Fly.io (or Vercel/Cloudflare) so the phone can reach it
- Configure Colota: endpoint URL, bearer token, tracking profile

**Done when:** Phone is silently logging to your database and you can query the points table.

### Phase 3 — Real data viewer
**Goal:** Replace fake-data loader with real API queries.

- Server endpoints for date-range and bounding-box filters
- Loading states, empty states, error handling
- The viewer designed in Phase 1, now reading real data

**Done when:** The viewer feels good with a few weeks of real data.

### Phase 4 — Backfill and refine (optional)
- Export Google Timeline via Takeout, convert, backfill into Postgres for historical context
- Add features as they call to you: trip detection, place clustering, "where was I a year ago today," annotations

### Phase 5 — Performance (only when it hurts)
- tippecanoe + tileserver-gl or martin
- Pre-aggregated heatmap tiles for "all-time" views
- Date-range partitioning if needed

---

## Default surface: a daily lens

Phase 1 focuses on the **per-day view** — opening the app shows one day's movements as a curated trip artifact (a route line with start/end markers, room to grow into time-of-segment labels, place icons, and other annotations in the lineage of [Felt's beautiful-map blog post](https://felt.com/blog/how-to-design-a-beautiful-map)). Date selection lives in a floating **calendar pill** at the top-left of the map: closed it shows the active date; opened it reveals a month grid where days with data are visually weighted by point count, so the calendar doubles as a discovery surface.

The earlier hypothesis of "heatmap of everything" as the default was *unset* during Phase 1 iteration. The reasoning, in short: Felt-style narrative artifacts are scoped — they assume *one* trip, intentionally curated. All-time personal location data is the inverse (thousands of overlapping movements, hundreds of stationary clusters) and a literal rendering of all of it is hostile to that aesthetic. Heatmap *is* the right answer to "where do I spend the most time," but it answers a different question than "where was I on this date" — and the per-date question is the more frequent one. So heatmap and other all-time surfaces are deferred until the daily lens is rich; full reasoning lives in `NOTES.md`.

## Other open design questions (for the viewer)

These don't have right answers — they're the things to decide *while building Phase 1* (and Phase 2/3 onward):

- **All-time surface (deferred):** Once the daily lens is rich, what does the all-time view become? Heatmap, calendar of trips, a place-cluster map, all of the above behind a toggle?
- **Search / query bar:** "Where was I when…", "trips over 2h," "places I've been 5+ times" — natural-language-ish querying. A much bigger product surface than the date picker; deferred until the daily lens settles.
- **Time scrubbing within a day:** A slider that animates progression through a single day's points? Or static "everything from this day at once"?
- **What is a "trip":** Auto-detect by time gaps and speed, user-defined, or not a concept at all? (A day is the rough unit for now; trips are a finer-grained question.)
- **Place rendering:** Cluster stationary points into named places? Show as icons on the daily lens? Auto-detect, manual tagging, or hybrid?
- **Outlier handling:** Filter by accuracy threshold? Show outliers in a different color? Ignore until it bites? (One 208 m/s GPS-jitter point already exists in the fixture.)
- **Custom Mapbox style:** Start from "Monochrome" or "Light" in Studio and modify, or build from scratch? (Currently using a custom Studio style; iteration ongoing.)

---

## Aesthetic references

- **Mapbox homepage and gallery** — palette, label density, considered restraint
- **Arc / Dia browser** — warm, off-white, serif-and-sans pairings
- **Linear, Notion, Paystack, Airbnb** — interaction craft, calm density
- **Dan Q's heatmap post** — the original inspiration, particularly the "personal record as artifact" framing

---

## What this project is not

- A fitness tracker
- A logistics tool
- A real-time tracker (with live "where am I now")
- A multi-user system
- A product

Naming this matters because every time a feature pulls toward one of these, it's pulling away from the actual project.

---

## Files in this project

- `static/points.geojson` — fake data for Phase 1, Mapbox-ready
- `static/points.json` — same data in the flat row shape that mirrors the eventual DB
- `generate_points.py` — regenerator if you want to tweak the fake data shape
- `src/lib/components/Map.svelte` — the map surface (full-bleed Mapbox, renders the selected day)
- `src/lib/components/CalendarPill.svelte` — floating date picker with point-count tinting

---

## For Claude Code (handoff notes)

If delegating implementation to an agent, scope tasks tightly. Good prompts:

- "Set up a SvelteKit JavaScript project with Mapbox GL JS, render `static/points.geojson` as a circle layer using the access token from `PUBLIC_MAPBOX_TOKEN`."
- "Add a date range filter that subsets the GeoJSON in memory and updates the map source."
- "Add a heatmap layer using the same source, weighted by point density."
- "Write a SvelteKit API route at `/api/track` that accepts POST requests in Colota's payload format and inserts into Neon. Validate a bearer token from `TRACK_AUTH_TOKEN`."

Bad prompts (do these by hand):

- "Build me a beautiful map view." (Generic AI aesthetic territory.)
- "Design the dashboard layout." (The design is the project.)
- "Pick a Mapbox style." (Taste decision.)

The architect role stays human. The agent does the typing.
