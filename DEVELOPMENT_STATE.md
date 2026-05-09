# DEVELOPMENT_STATE

Per-session handoff. The point of this file is that the *next* session — yours, mine, or any LLM's — can pick up cold without re-deriving where things are.

This is **not** a roadmap or a north star. The north star lives in `PROJECT.md`; the thinking-in-flight lives in `NOTES.md`. This file just records what was built, in which session, with what files touched, and how to verify it works.

Sessions stack chronologically. Old entries don't get deleted — they're how you reconstruct what was known when.

---

## Session 1 — Phase 1 viewer: scaffold, two false starts, pivot to heatmap with cubic weighting

**Why:** Phase 1 of PROJECT.md is "viewer with fake data," with the explicit goal of *discovering* what the viewer should be. This session ran four iterations of the visualization and landed on heatmap-as-default with Dan Q-style cubic weighting. Full reasoning lives in `NOTES.md`; the relevant threads are "Default visualization: heatmap won," "Why literal points and lines lost," and "Cubic weighting matters."

**What got built:**

- A SvelteKit + Mapbox GL JS scaffold. `src/lib/components/Map.svelte` mounts a full-bleed Mapbox map in `onMount` (Mapbox can't SSR), reads the fake GeoJSON fixture, and renders one heatmap layer on top of a custom Mapbox Studio style.
- The token convention is `PUBLIC_MAPBOX_TOKEN` (renamed from `MAPBOX_TOKEN` so `$env/static/public` exposes it client-side; Mapbox public tokens are designed to ship to the browser).
- The current heatmap pre-buckets points by coordinates rounded to 5 decimal places (~1.1 m precision), counts visits per cell, and sets each cell's `weight = (count / maxCount)^3` — Dan Q's exponential weighting ported to Mapbox's native heatmap.
- Color ramp: a "dusk" palette (transparent → pale lavender → mauve → twilight violet → deep indigo → midnight). Chosen to avoid SaaS-generic purples; pending visual validation by the user.

**Files touched:**

- `src/lib/components/Map.svelte` (new) — the entire map component.
- `src/routes/+page.svelte` — stripped SvelteKit boilerplate, renders `<Map />`.
- `src/routes/+layout.svelte` — added `import 'mapbox-gl/dist/mapbox-gl.css'` and global `html, body { height: 100%; margin: 0 }`.
- `package.json`, `bun.lock` — added `mapbox-gl ^3.23.0`.
- `.env` — `PUBLIC_MAPBOX_TOKEN=...` (renamed from `MAPBOX_TOKEN`).

**Iterations within this session (committed and uncommitted):**

1. Scaffold with default circles. Committed: `fc1983c — Scaffold Mapbox view rendering points.geojson`.
2. Points colored by speed (warm-monochrome ramp). Felt muddy. Not committed; superseded.
3. Faint terracotta line + dark ember dots. Stationary clusters became visual tangles. Not committed; superseded.
4. Pivot to heatmap with linear summation. Looked uniformly purple — the color stops were too compressed and the data too uniform. Not committed; superseded.
5. **Current state:** heatmap with cubic weighting + dusk palette. Uncommitted. Awaits user reload and visual judgment.

**Test checkpoint:**

```sh
bun install   # if mapbox-gl isn't already installed
bun run dev
```

Open `http://localhost:5173`. You should see a full-viewport Mapbox map fitted to the bounds of the fake data, with a heatmap overlay. The cubic-weighted version will show small bright lavender/indigo spots at the most-visited cells (counts of 9–14 in the current fixture) and near-transparent everywhere else — see the "Cubic weighting" thread in `NOTES.md` for why this is a fixture problem rather than a visualization problem.

**Carrying into the next session:**

- **The fake fixture is the wrong shape for the visualization, and is the gating issue.** `static/points.geojson` was generated as roughly uniform wandering — most cells visited once, max 14 visits at any cell, no real "anchor" places. The heatmap (with or without cubic weighting) is designed for hotspot-rich data: a desk visited a thousand times competing with a road driven once. On this fixture there's no hotspot signal worth visualizing, and every downstream visual decision (color stops, intensity, radius, weighting exponent) is being made against data that doesn't exercise the design.
  - **Next concrete action:** modify `generate_points.py` to produce a bimodal distribution — 60–70% of points clustered at 2–3 fake "places" (home, office, a regular third place), 30–40% on travel routes between them. Then regenerate `static/points.geojson` and `static/points.json`.
  - **Visual tuning is paused** (color ramp, intensity, radius, exponent) until the fixture is replaced. Tuning before that is wasted motion.
  - Reasoning lives in the "Cubic weighting matters, but it needs hotspot-rich data" thread in `NOTES.md`.
- User has not yet validated the cubic-pass result visually. Reload pending. But given the data-shape issue above, that judgment will be against a fixture we already know is wrong; useful only as a sanity check that the layer renders, not as a verdict on the visualization.
- Color: dusk palette unvalidated. If it doesn't land, alternative directions (oceanic, monochrome warm, two-tone) noted in `NOTES.md`. But — same caveat — this judgment also waits on real-shaped data.

---

## Session 2 — Pivot to daily-lens default + floating calendar pill

**Why:** Session 1 landed on heatmap-as-default with literal renderings as filtered lenses, but the heatmap kept feeling wrong even after fixture regeneration. User surfaced [Felt's "How to design a beautiful map" post](https://felt.com/blog/how-to-design-a-beautiful-map) — annotated trail maps with route lines, time labels, place icons, photo embeds — and asked whether to switch to Felt's API and use that style as the default.

The reframe: Felt's API is the wrong tool (Felt is built *on* Mapbox GL JS, their API is for embedding hosted maps), and Felt-style aesthetics are *scoped narrative artifacts*, not all-time views. The user's two queries split cleanly — "where was I on this date" → daily lens, "where do I spend the most time" → heatmap. The daily question is more frequent *and* carries the aesthetic weight. So Phase 1 narrowed: build the daily lens. All-time / heatmap deferred. Full thread in `NOTES.md` ("The Felt reframe").

**What got built:**

- `src/lib/components/CalendarPill.svelte` (new) — floating date-picker pill (top-left of the map). Closed: shows the active date; clicked: expands into a month grid where days with data are background-tinted by point count (terracotta, opacity scaled by `count / maxCount`). Selected day is filled terracotta. Keyboard: arrow keys move focus, Enter selects, Esc closes. Click-outside dismisses. No type-to-jump in v1 (deferred — see NOTES "The calendar pill: discovery beats command-palette").
- `src/lib/components/Map.svelte` (rewritten from heatmap) — groups all points by `YYYY-MM-DD` on load, computes per-day counts for the calendar, and renders the *selected* day as: a terracotta line (3px, rounded caps/joins) with a soft 8px shadow line beneath for depth, plus start/end circle markers (filled vs ringed). Re-fits bounds on date change (animated 600ms; first render is instant to avoid spinning out of [0,0]).
- All heatmap rendering deleted. Saved in commit `a4fa9e8` if needed for resurrection.

**Initial selected date:** the most-populated day in the fixture (currently `2026-04-16`, 230 points). For the demo this lands on something visually rich. **When real Colota data flows, swap to "most-recent day with data"** — see NOTES "The 'initial date' question."

**Files touched:**

- `src/lib/components/CalendarPill.svelte` — new.
- `src/lib/components/Map.svelte` — full rewrite (heatmap → daily route + endpoints, calendar mounted as sibling overlay so the Mapbox container stays empty).
- `PROJECT.md` — graduated the daily-view-first decision; added new files to "Files in this project"; restructured the open-design-questions section.
- `NOTES.md` — added "The Felt reframe" thread; unsettled "Default visualization: heatmap won"; marked cubic-weighting and dusk-color threads `[ON HOLD — heatmap deferred]`; promoted "icons-for-places" relevance; added "The calendar pill: discovery beats command-palette" and "The 'initial date' question" threads; refreshed open-threads list (time-gap breaking and outlier handling are now load-bearing for the daily lens, not just the heatmap escape hatch).

**Test checkpoint:**

```sh
bun run dev
```

Open `http://localhost:5173`. You should see:

1. The map full-bleed, fitted to the bounds of one day's points (the most-populated day).
2. A terracotta line tracing the day's path, with a soft shadow beneath, start/end markers at either end (filled circle = start, white-with-ring = end).
3. A floating date pill top-left ("Apr 16, 2026"). Click it → month calendar overlay; days with data have a faint terracotta background, scaled by point count.
4. Click another day → the route updates and bounds re-fit (animated). Esc closes. Arrow keys + Enter work for keyboard nav.

**Known unknowns (for the next session):**

- **Visual judgment on the line color (`#c45a3d` terracotta) and weight is pending.** Picked as a tasteful starting point, fully expecting iteration. Alternatives if it doesn't land: warmer red, deeper rust, a muted ember-green (Mapbox-homepage-style).
- **Outlier handling is now load-bearing.** The 208 m/s GPS-jitter point on a literal line draws a long diagonal arm across the bounds — much more disruptive than on a heat surface. Probably wants an `accuracy <= N` filter before constructing the LineString. Pick threshold by inspection.
- **Time-gap breaking inside a day.** Even within one day, a phone-off-in-pocket gap will draw a nonsense diagonal across whatever route the user traveled in between. Threshold likely 15–30 min.
- **No "what day is this" caption yet.** The pill shows the date, but a small readout of point count + time span (e.g. "230 points · 06:00 → 22:45") would ground the user. Defer until the basic interaction feels right.
- **Type-to-jump in the calendar overlay.** Deferred — natural to add a small text field at the top of the calendar accepting "yesterday" / "apr 13" once the rest settles.
- **Initial date should swap from "most-populated" to "most-recent" when real data flows** — flagged so it doesn't get forgotten.

**Carrying into the next session:**

- User reload + visual judgment on the daily-lens result (color, line weight, marker style, calendar tint visibility).
- If line color lands, next concrete iterations are: outlier filter, time-gap segmentation, then a small day-readout caption.
- The "icons-for-places" thread (NOTES) is the next significant aesthetic layer once the route itself feels good — Felt's lunch-break pizza, peak markers, etc.
- All-time / heatmap surface stays parked. Will be revisited when the daily lens carries its own weight.
