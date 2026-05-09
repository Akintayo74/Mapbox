# NOTES

A working notebook. Open threads, evolving hypotheses, reframings — the *thinking* behind decisions, not the decisions themselves.

This file is **not** a spec. The spec lives in `PROJECT.md` (which plays the role of `PRODUCT_SPEC.md` in the three-doc workflow — same role, different name). When a thread here settles into doctrine, it graduates over to `PROJECT.md` and gets stripped from here. Per-session changes and concrete handoff state live in `DEVELOPMENT_STATE.md`.

If a thread below reads as settled and prescriptive, that's a smell: either move it to the spec or restore the open-question framing.

---

## Default visualization: heatmap was the answer, until it wasn't — daily lens took over

**Status:** thread *unsettled* in Session 2. Originally landed on "heatmap as default canvas, lens-switching to dots and lines for filtered subsets." The lens half is now the focus; the heatmap-as-default half is on hold. See "The Felt reframe" thread below for the reasoning.

The original journey is still worth keeping for context: Session 1 opened with the implicit frame "let's render points." That's what the existing scaffold did — circles on a map, with color-by-speed eventually. PROJECT.md actually names Dan Q's heatmap post as "the original inspiration" verbatim, but the agent went to literal points and lines without ever proposing heatmap as the primary option. The user surfaced it. Lesson worth carrying: when PROJECT.md names an inspiration explicitly, that's a strong prior on direction.

## Why literal points and lines lost on this data

Two attempts. The first was points-colored-by-speed with a warm-monochrome ramp (sand → amber → terracotta → ember). It came out muddy — the warm family collapsed into low-contrast brown sludge, and the visualization was fighting the data: roughly 50% of points sit below 0.32 m/s (essentially stationary), so half the dataset crowded into the "slow" color regardless of which color that was.

The second was a faint line beneath dark ember dots. The line was meant to give continuity (where you went) and the dots gave moments (where you were). The stationary clusters became visual tangles of GPS jitter — lines are great for movement, useless for sitting at a desk for six hours.

Both attempts hit the same wall: literal renderings are hostile to data dominated by stillness. They render time as visual weight, but in a noisy, clumsy way.

## Why heatmap dissolves the problem

The shift isn't "different visualization" — it's a different *question*. Literal points ask "where is each fix?" Heatmap asks "how dense is presence here?" Once you stop asking the literal question, the bimodality (stationary vs moving) stops being a problem and becomes the feature: a desk visited a thousand times glows; a road driven once is faint. GPS jitter at home becomes one warm bloom rather than fifty noisy points — that's honesty, not lossiness. The PROJECT.md framing of the project as "personal record as artifact" fits heatmap better than literal renderings ever did.

## The Felt reframe: trip-style artifacts are scoped, not all-time

**Graduated to PROJECT.md in Session 2.** Kept here because the *reasoning* is what future sessions will need to revisit — the doctrine in PROJECT.md is just the answer.

Session 2 opened with the user dissatisfied with the heatmap (even after regenerating the fixture), and pointing at two examples from Felt's "How to design a beautiful map" blog post — annotated trail maps with route lines, time-on-segment labels, lunch-break pizza icons, peak markers, photo embeds, area highlights for wildfire history. The opening question was: switch to Felt's API, and use this as the default map experience?

Two pieces of pushback landed:

1. **Felt's API is the wrong tool.** Felt is *built on* Mapbox GL JS — Mapbox is the rendering library underneath. Felt's API is for embedding hosted maps you've designed in their editor, not for programmatic rendering. Everything in those screenshots is achievable with Mapbox primitives (line layers, symbol layers, fill layers, hillshade, custom HTML markers). Switching costs more than it gains.

2. **Felt-style maps are *scoped narrative artifacts*, not all-time views.** Each Felt example is one hike, intentionally curated, with hand-placed annotations. The aesthetic *requires* curation. All-time personal location data is the inverse — thousands of overlapping movements, hundreds of stationary clusters — and rendering that literally would be a tangled brown mess. The Felt aesthetic and the all-time data shape are pointing in different directions.

The unlock was noticing the user's two stated queries split cleanly:

- *"Where was I on particular dates"* → date filter → Felt-style trip view (the literal lens)
- *"Where I spent the most time"* → density across all-time → heatmap (or a place-cluster surface)

So the daily lens isn't a competitor to the heatmap — they answer different questions. But the daily question is the more frequent one *and* it carries the aesthetic weight of the project (Arc, Linear, Notion, Mapbox homepage are all curated-single-thing surfaces). So Phase 1's design focus narrows: build the daily lens until it's beautiful. The all-time surface waits.

Practical consequence: heatmap code is being deleted (saved in commit `a4fa9e8`, easy to resurrect). Visual tuning threads on the heatmap (color, intensity, cubic exponent) go on hold. The "icons-for-places" thread becomes more relevant since annotations are the natural next layer once a route renders.

## Default heatmap, lens-switching to dots and lines for filtered subsets

**Superseded in Session 2** by "The Felt reframe" thread above. Originally settled in Session 1: heatmap by default, literal renderings as scoped lenses. The lens half stayed (and grew); the default-heatmap half is now on hold.

Original framing kept here for context: heatmap was the canvas you see when you open the app — all your data, all the time, the shape of your life. When you scope down (a single day, a single trip, a place), heatmap loses meaning — one trip is not a heat surface — and that's when literal points and lines take over as the right visualization for the question you're asking. The reasoning still holds for the lens half; what changed is the user's appetite for "all your data, all the time" as the *first thing you see*. That ask was bigger than the visualization could carry.

## Mapbox's heatmap is not Dan Q's heatmap, and there's an escape hatch

Dan uses heatmap.js with `useLocalExtrema: true` — the color scale rebases to the visible viewport's max, so when you zoom into a quiet area that area's local max becomes "bright." Mapbox GL JS native heatmap uses global extrema; the closest approximation Mapbox gives us is interpolating `heatmap-intensity` by zoom (intensity ramps up as you zoom in so per-pixel density doesn't fade out). It approximates but isn't the same.

If we hit a wall the native heatmap can't solve, the escape hatch is heatmap.js layered over a Mapbox style, or pre-rendered tippecanoe tiles. Both are deferred — consistent with PROJECT.md's "no tippecanoe yet" — and we don't switch until native genuinely hurts.

## Cubic weighting matters, but it needs hotspot-rich data to show its effect [ON HOLD — heatmap deferred]

Dan raises frequency to the power of 3 to make hotspots exponentially brighter than warm spots. We ported this: bucket points by rounded coordinates (5 decimal places, ~1.1 m), count points per cell, set `weight = (count/maxCount)^3`, feed into `heatmap-weight`. The math is sound.

But the fake fixture has a problem. The most-visited cell has 14 points; 77% of cells are visited only once. After cubing, the dynamic range is dominated by a handful of cells while almost everything else collapses to near-zero weight. The heatmap renders a few small bright spots and near-transparent everywhere else.

This isn't the visualization being wrong — it's the visualization being faithful to a fixture that doesn't have the shape it was designed for. Real personal-location data over weeks has cells visited *hundreds* of times (a desk, a bed) competing with cells visited once or twice (a road driven once); the cubic ratio there is enormous and the heatmap pops. The fake data simulates "wandering without a home base" rather than "a life with anchors."

**Decided, action pending:** the fixture is wrong-shaped for what we're building, and we will regenerate it. `generate_points.py` needs to produce a realistic bimodal distribution — roughly 60–70% of points clustered at 2–3 fake "places" (a home, an office, maybe a regular-third-place), 30–40% spread along travel routes between them. The point is not that the fake data look exactly like real life, but that it has the *shape* the visualization is built for: a few cells visited hundreds of times competing with many cells visited once or twice. Without that shape, every visual tuning decision (color stops, intensity, radius, exponent) is being made against a fixture that doesn't exercise the design — wasted motion that won't transfer when real Colota data starts flowing.

This is the next concrete move in Phase 1. Visual tuning is paused until the fixture is replaced. Tracked in `DEVELOPMENT_STATE.md` as the action item carrying into the next session.

## Color: warm didn't land, dusk is the current attempt, jury still out [ON HOLD — heatmap deferred]

Two warm-monochrome palettes felt muddy and SaaS-generic to the user. The current attempt is "dusk" — pale lavender → mauve → twilight violet → deep indigo → midnight, anchored on the gradient of a sky between sunset and night. The deliberate move was to avoid the Linear/Stripe/Tailwind cyan-leaning brand purples (the SaaS lane the user explicitly didn't want); real-flower lavender at the faint end has slight warmth, and the deep end is true night-sky indigo with weight to it.

Risk yet to resolve: if the basemap (custom Mapbox Studio style) runs dark, the deep end of the gradient collides with it. Pending the next reload's verdict.

If dusk doesn't land either, directions to try: oceanic (transparent → ultramarine → deep navy — straightforwardly cool, less violet), monochrome warm (single hue varying only in opacity — calmer), or two-tone (pale gold → deep red, skipping the middle entirely).

## The icons-for-places idea is real, but "what is a place" comes first

The user asked early in Session 1 whether named places (home, work) could render as icons rather than dots. Mapbox supports symbol layers backed by `map.addImage()` — technically straightforward. The real work is defining what counts as a place. Three paths: auto-detect by clustering stationary points (works without input but you don't get to name them), manual tagging (slow to set up but the names are yours), or hybrid (auto-cluster, you label the ones that matter).

**Promoted in priority by Session 2's Felt reframe.** With the daily lens as the active surface, icons-as-places are no longer "punctuation on top of the heat" — they're the *next natural layer* on top of the route. Felt's second screenshot shows exactly this shape: a route with a pizza icon for the lunch break, a peak icon for Echo Peak, a campsite icon at the end. Each is a place that the route happens to pass through, labelled in context.

The "what counts as a place" question is still the gate. Hybrid (auto-detect candidates, user confirms/labels) is probably right — auto-detection alone gives you "the centroid of a stationary cluster" with no name, which is just a worse dot. But that's all deferred until the route + calendar are landed and feel good.

## The calendar pill: discovery beats command-palette

Decision in Session 2 to use a click-to-expand month-grid pill rather than a Linear-style command bar (`type "yesterday"` / `"apr 13"`). The tradeoff: a calendar takes more screen real estate, but it surfaces *which days have data* — the calendar itself doubles as a navigation surface, with each day visually weighted by point count. A command palette only helps when you already know the date you want; for personal cartography, a lot of the value is in stumbling over a Tuesday from three weeks ago and remembering what you did. So discovery > speed for the default interaction.

Type-to-jump support is deferred but not dead. Once the calendar lands, a small text field at the top of the open calendar that accepts "yesterday" / "apr 13" / "last sunday" is a natural addition — gives keyboard users speed without sacrificing discovery for everyone else. Punted on this for v1 to avoid building a parser before knowing if we want one.

The search bar (broader than date) is deferred further. "Where was I when…", "trips over 2h," "places I've been 5+ times" is natural-language-ish querying — a much bigger product surface, and we don't yet know which queries are the load-bearing ones. Better to land the date picker first and learn what people (well, the user) actually want to ask.

## The "initial date" question

The first date the app loads on. Two natural choices:

- **Most recent day with data** — what real users will want once Colota is flowing (you opened the app to see *today*).
- **Most-populated day** — what the demo wants now (gives the visualization something visually rich to land on).

Picked most-populated for the fixture-driven phase, with the explicit understanding that this swaps to "most recent" once real data flows. Worth flagging in DEVELOPMENT_STATE so the swap doesn't get forgotten.

## Other open threads to keep live

- **Time-gap breaking** for the line layer: real data will have gaps where the phone was off, and a single connected line draws nonsense diagonals across hundreds of km. Threshold probably 15–30 min, decided when we hit it. Within a single day this is rarer than across days, but a phone-off-in-pocket scenario can still produce one — worth handling early in the daily lens, not late.
- **Outlier handling**: a 208 m/s point exists in the current fixture (GPS jitter). On a daily-lens line, one wild point will draw a long diagonal arm across the whole bounds. Accuracy thresholding (drop points over some `accuracy` value) probably becomes load-bearing earlier than expected once we're rendering literal lines.
- **Time scrubbing within a day**: a slider that animates progression through the selected day's points? Tied to "what is a trip" question. Not designed yet.
- **Trip detection**: speed + time-gap auto-detection, user-defined trips, or "not a concept at all"? Open. A day is the rough unit for now; finer-grained trip segmentation is a separate question.
- **Time-of-day light presets** (user's earlier ask): can the Mapbox style swap automatically — dawn preset at dawn, dusk preset at dusk, stop at dusk because user dislikes the night preset? Mapbox Standard style supports `light` config (`'dawn' | 'day' | 'dusk' | 'night'`) — needs investigation. More relevant now that the daily lens is the active surface and the basemap matters more.

## A hypothesis we walked away from

Early in the session, the working assumption was that color-by-speed is a meaningful encoding for personal cartography — the idea being that movement type (stationary, walking, driving) should be visually legible. The session moved past this. Speed as a color encoding fights the heatmap (which is about density, not movement type), and it duplicates information already implicit in the *shape* of the data (driving traces are long-and-linear, stationary clusters are small-and-dense). Color budget is better spent on density alone.

Speed may still earn a place when filtering to a single trip in the lens view — but as a *default* encoding on the all-time map, it's been retired.
