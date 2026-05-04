# NOTES

A working notebook. Open threads, evolving hypotheses, reframings — the *thinking* behind decisions, not the decisions themselves.

This file is **not** a spec. The spec lives in `PROJECT.md` (which plays the role of `PRODUCT_SPEC.md` in the three-doc workflow — same role, different name). When a thread here settles into doctrine, it graduates over to `PROJECT.md` and gets stripped from here. Per-session changes and concrete handoff state live in `DEVELOPMENT_STATE.md`.

If a thread below reads as settled and prescriptive, that's a smell: either move it to the spec or restore the open-question framing.

---

## Default visualization: heatmap won, but the path to it was via two false starts

The session opened with the implicit frame "let's render points." That's what the existing scaffold did — circles on a map, with color-by-speed eventually. PROJECT.md actually names Dan Q's heatmap post as "the original inspiration" verbatim, but the agent went to literal points and lines without ever proposing heatmap as the primary option. The user surfaced it.

Worth saying out loud: heatmap should have been the first proposal, not the third. The two literal attempts weren't waste — they exposed something real about the data — but the path was longer than it needed to be. Lesson worth carrying: when PROJECT.md names an inspiration explicitly, that's a strong prior on direction.

## Why literal points and lines lost on this data

Two attempts. The first was points-colored-by-speed with a warm-monochrome ramp (sand → amber → terracotta → ember). It came out muddy — the warm family collapsed into low-contrast brown sludge, and the visualization was fighting the data: roughly 50% of points sit below 0.32 m/s (essentially stationary), so half the dataset crowded into the "slow" color regardless of which color that was.

The second was a faint line beneath dark ember dots. The line was meant to give continuity (where you went) and the dots gave moments (where you were). The stationary clusters became visual tangles of GPS jitter — lines are great for movement, useless for sitting at a desk for six hours.

Both attempts hit the same wall: literal renderings are hostile to data dominated by stillness. They render time as visual weight, but in a noisy, clumsy way.

## Why heatmap dissolves the problem

The shift isn't "different visualization" — it's a different *question*. Literal points ask "where is each fix?" Heatmap asks "how dense is presence here?" Once you stop asking the literal question, the bimodality (stationary vs moving) stops being a problem and becomes the feature: a desk visited a thousand times glows; a road driven once is faint. GPS jitter at home becomes one warm bloom rather than fifty noisy points — that's honesty, not lossiness. The PROJECT.md framing of the project as "personal record as artifact" fits heatmap better than literal renderings ever did.

## Default heatmap, lens-switching to dots and lines for filtered subsets

The most important reframing of the session. Heatmap is the canvas you see when you open the app — all your data, all the time, the shape of your life. When you scope down (a single day, a single trip, a place), heatmap loses meaning — one trip is not a heat surface — and that's when literal points and lines take over as the right visualization for the question you're asking.

So dots and lines aren't dead, they're the *filtered-lens* visualization, not the default. PROJECT.md flagged this in its "Default view" open question, and we've answered it: heatmap by default, with literal renderings as scoped lenses. This thread is settled enough that the relevant section of PROJECT.md ("Default view: Last 7 days? Last month? 'Today'? A heatmap of everything?") could be updated to reflect the answer.

## Mapbox's heatmap is not Dan Q's heatmap, and there's an escape hatch

Dan uses heatmap.js with `useLocalExtrema: true` — the color scale rebases to the visible viewport's max, so when you zoom into a quiet area that area's local max becomes "bright." Mapbox GL JS native heatmap uses global extrema; the closest approximation Mapbox gives us is interpolating `heatmap-intensity` by zoom (intensity ramps up as you zoom in so per-pixel density doesn't fade out). It approximates but isn't the same.

If we hit a wall the native heatmap can't solve, the escape hatch is heatmap.js layered over a Mapbox style, or pre-rendered tippecanoe tiles. Both are deferred — consistent with PROJECT.md's "no tippecanoe yet" — and we don't switch until native genuinely hurts.

## Cubic weighting matters, but it needs hotspot-rich data to show its effect

Dan raises frequency to the power of 3 to make hotspots exponentially brighter than warm spots. We ported this: bucket points by rounded coordinates (5 decimal places, ~1.1 m), count points per cell, set `weight = (count/maxCount)^3`, feed into `heatmap-weight`. The math is sound.

But the fake fixture has a problem. The most-visited cell has 14 points; 77% of cells are visited only once. After cubing, the dynamic range is dominated by a handful of cells while almost everything else collapses to near-zero weight. The heatmap renders a few small bright spots and near-transparent everywhere else.

This isn't the visualization being wrong — it's the visualization being faithful to a fixture that doesn't have the shape it was designed for. Real personal-location data over weeks has cells visited *hundreds* of times (a desk, a bed) competing with cells visited once or twice (a road driven once); the cubic ratio there is enormous and the heatmap pops. The fake data simulates "wandering without a home base" rather than "a life with anchors."

**Decided, action pending:** the fixture is wrong-shaped for what we're building, and we will regenerate it. `generate_points.py` needs to produce a realistic bimodal distribution — roughly 60–70% of points clustered at 2–3 fake "places" (a home, an office, maybe a regular-third-place), 30–40% spread along travel routes between them. The point is not that the fake data look exactly like real life, but that it has the *shape* the visualization is built for: a few cells visited hundreds of times competing with many cells visited once or twice. Without that shape, every visual tuning decision (color stops, intensity, radius, exponent) is being made against a fixture that doesn't exercise the design — wasted motion that won't transfer when real Colota data starts flowing.

This is the next concrete move in Phase 1. Visual tuning is paused until the fixture is replaced. Tracked in `DEVELOPMENT_STATE.md` as the action item carrying into the next session.

## Color: warm didn't land, dusk is the current attempt, jury still out

Two warm-monochrome palettes felt muddy and SaaS-generic to the user. The current attempt is "dusk" — pale lavender → mauve → twilight violet → deep indigo → midnight, anchored on the gradient of a sky between sunset and night. The deliberate move was to avoid the Linear/Stripe/Tailwind cyan-leaning brand purples (the SaaS lane the user explicitly didn't want); real-flower lavender at the faint end has slight warmth, and the deep end is true night-sky indigo with weight to it.

Risk yet to resolve: if the basemap (custom Mapbox Studio style) runs dark, the deep end of the gradient collides with it. Pending the next reload's verdict.

If dusk doesn't land either, directions to try: oceanic (transparent → ultramarine → deep navy — straightforwardly cool, less violet), monochrome warm (single hue varying only in opacity — calmer), or two-tone (pale gold → deep red, skipping the middle entirely).

## The icons-for-places idea is real, but "what is a place" comes first

The user asked early in the session whether named places (home, work) could render as icons rather than dots. Mapbox supports symbol layers backed by `map.addImage()` — technically straightforward. The real work is defining what counts as a place. Three paths: auto-detect by clustering stationary points (works without input but you don't get to name them), manual tagging (slow to set up but the names are yours), or hybrid (auto-cluster, you label the ones that matter).

PROJECT.md flags this as an open design question. With heatmap as the default surface, icons-as-places becomes punctuation on top of the heat — labels for what the heat is already showing — rather than a competing visualization. Defer until heatmap is working with realistic data.

## Other open threads to keep live

- **Time-gap breaking** for the line layer (when filtered): real data will have gaps where the phone was off, and a single connected line draws nonsense diagonals across hundreds of km. Threshold probably 15–30 min, decided when we hit it.
- **Outlier handling**: a 208 m/s point exists in the current fixture (GPS jitter). Doesn't move the heat surface meaningfully (one wild point in 2800), but accuracy filtering will eventually matter for the dots-and-lines lens.
- **Time scrubbing UI**: slider, calendar picker, both? Tied to whatever filter UI ends up being. Not designed yet.
- **Trip detection**: speed + time-gap auto-detection, user-defined trips, or "not a concept at all"? Open. PROJECT.md flags this.
- **Time-of-day light presets** (user's earlier ask): can the Mapbox style swap automatically — dawn preset at dawn, dusk preset at dusk, stop at dusk because user dislikes the night preset? Mapbox Standard style supports `light` config (`'dawn' | 'day' | 'dusk' | 'night'`) — needs investigation. Worth checking once the heatmap is settled.

## A hypothesis we walked away from

Early in the session, the working assumption was that color-by-speed is a meaningful encoding for personal cartography — the idea being that movement type (stationary, walking, driving) should be visually legible. The session moved past this. Speed as a color encoding fights the heatmap (which is about density, not movement type), and it duplicates information already implicit in the *shape* of the data (driving traces are long-and-linear, stationary clusters are small-and-dense). Color budget is better spent on density alone.

Speed may still earn a place when filtering to a single trip in the lens view — but as a *default* encoding on the all-time map, it's been retired.
