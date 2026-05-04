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
