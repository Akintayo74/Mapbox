"""
Generate fake location points for Akintayo's map viewer testing.

Produces points.json (flat array, matches what a real DB table would look like)
and points.geojson (Mapbox-ready FeatureCollection derived from the above).
"""

import json
import math
import random
from datetime import datetime, timedelta, timezone

random.seed(42)  # reproducible output

# Anchor locations (verified via Google Places)
HOME = (9.9439278, 8.8619029)         # Rock Haven Street
IXNOTE = (9.8518618, 8.8671170)       # Hill Station Junction (Wase Court area)
GIEVA = (9.9089580, 8.8906282)        # Challenge Bookshop, Beach Road
ABUJA_CENTER = (9.0579, 7.4951)       # Central Business District
LAGOS_VI = (6.4281, 3.4219)           # Victoria Island
CALABAR_CENTER = (4.9757, 8.3417)     # Calabar municipality

WAT = timezone(timedelta(hours=1))    # West Africa Time, no DST


def jitter(point, meters=15):
    """Add small random offset to simulate GPS noise. ~111km per degree lat."""
    lat, lon = point
    lat_offset = random.gauss(0, meters / 111_000)
    lon_offset = random.gauss(0, meters / (111_000 * math.cos(math.radians(lat))))
    return (lat + lat_offset, lon + lon_offset)


def interpolate(start, end, n):
    """Linear interpolation between two points, n intermediate points."""
    return [
        (start[0] + (end[0] - start[0]) * t / (n + 1),
         start[1] + (end[1] - start[1]) * t / (n + 1))
        for t in range(1, n + 1)
    ]


def make_point(lat, lon, ts, speed_kmh=0, accuracy=10, altitude=1200, battery=80):
    """Construct a point dict in Colota-ish shape."""
    return {
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "timestamp": ts.isoformat(),
        "accuracy": round(accuracy, 1),
        "speed": round(speed_kmh / 3.6, 2),  # stored as m/s
        "bearing": round(random.uniform(0, 360), 1),
        "altitude": altitude,
        "battery": battery,
    }


def trip(start_loc, end_loc, start_time, duration_minutes, n_points,
         speed_kmh=30, accuracy=10, altitude=1200, battery_start=80):
    """Generate a sequence of points along a trip from start to end."""
    points = []
    intermediate = interpolate(start_loc, end_loc, n_points - 2)
    locations = [start_loc] + intermediate + [end_loc]
    seconds_per_point = (duration_minutes * 60) / (n_points - 1)
    for i, loc in enumerate(locations):
        ts = start_time + timedelta(seconds=i * seconds_per_point)
        # gentle battery drain across the trip
        battery = max(20, int(battery_start - i * 0.1))
        # slight speed variation
        actual_speed = max(0, speed_kmh + random.gauss(0, speed_kmh * 0.15))
        jittered = jitter(loc, meters=accuracy * 0.6)
        points.append(make_point(
            jittered[0], jittered[1], ts,
            speed_kmh=actual_speed, accuracy=accuracy,
            altitude=altitude, battery=battery,
        ))
    return points


def stationary(loc, start_time, duration_minutes, point_every_minutes=5,
               accuracy=8, altitude=1200, battery=70):
    """Generate stationary points (e.g., at work, teaching, sleeping)."""
    points = []
    n = max(1, int(duration_minutes / point_every_minutes))
    for i in range(n):
        ts = start_time + timedelta(minutes=i * point_every_minutes)
        # tighter jitter for stationary - just GPS drift
        jittered = jitter(loc, meters=5)
        points.append(make_point(
            jittered[0], jittered[1], ts,
            speed_kmh=random.uniform(0, 1.5),  # tiny non-zero, realistic
            accuracy=accuracy, altitude=altitude, battery=battery,
        ))
    return points


# -----------------------------------------------------------------------------
# Build the dataset: ~3 weeks of life + 2 long-distance trips
# -----------------------------------------------------------------------------

all_points = []

# Start date: April 13, 2026 (a Monday) - 3 weeks of data
base_date = datetime(2026, 4, 13, 0, 0, tzinfo=WAT)

# --- A typical Jos work week: Mon-Fri commute + Tue/Thu evening teaching ---
for week in range(2):  # 2 full work weeks
    for weekday in range(5):  # Mon-Fri
        day = base_date + timedelta(days=week * 7 + weekday)

        # Morning at home
        all_points += stationary(HOME, day.replace(hour=6, minute=0),
                                 duration_minutes=90, battery=95)

        # Commute Rock Haven -> Hill Station Junction
        all_points += trip(HOME, IXNOTE,
                           day.replace(hour=7, minute=45),
                           duration_minutes=35, n_points=22,
                           speed_kmh=28)

        # At Ixnote office
        all_points += stationary(IXNOTE, day.replace(hour=8, minute=30),
                                 duration_minutes=8 * 60, battery=70)

        # Tue/Thu: stop at GIEVA on the way home
        if weekday in (1, 3):
            all_points += trip(IXNOTE, GIEVA,
                               day.replace(hour=16, minute=45),
                               duration_minutes=20, n_points=14,
                               speed_kmh=25)
            # Teaching session
            all_points += stationary(GIEVA, day.replace(hour=17, minute=10),
                                     duration_minutes=120, battery=50)
            all_points += trip(GIEVA, HOME,
                               day.replace(hour=19, minute=15),
                               duration_minutes=22, n_points=15,
                               speed_kmh=22)
        else:
            # Direct home
            all_points += trip(IXNOTE, HOME,
                               day.replace(hour=17, minute=0),
                               duration_minutes=30, n_points=18,
                               speed_kmh=27)

        # Evening at home
        all_points += stationary(HOME, day.replace(hour=20, minute=0),
                                 duration_minutes=10 * 60,
                                 point_every_minutes=15, battery=40)

# --- A weekend walk around Rock Haven neighborhood (Saturday week 1) ---
sat = base_date + timedelta(days=5)
walk_start = sat.replace(hour=7, minute=0)
# Walking loop: short hops, slow speeds, lots of small turns
walk_waypoints = [
    HOME,
    (9.9445, 8.8625),
    (9.9460, 8.8635),
    (9.9472, 8.8628),
    (9.9468, 8.8615),
    (9.9450, 8.8610),
    HOME,
]
for i in range(len(walk_waypoints) - 1):
    seg_start = walk_start + timedelta(minutes=i * 12)
    all_points += trip(walk_waypoints[i], walk_waypoints[i + 1],
                       seg_start, duration_minutes=12, n_points=14,
                       speed_kmh=5, accuracy=6)

# --- Trip to Abuja, Lagos (week 3) ---
# Drive Jos -> Abuja, fly Abuja -> Lagos, return same way
trip_start_day = base_date + timedelta(days=14)  # Monday week 3

# Jos -> Abuja drive (~4 hours, 280km)
all_points += trip(HOME, ABUJA_CENTER,
                   trip_start_day.replace(hour=6, minute=0),
                   duration_minutes=240, n_points=80,
                   speed_kmh=70, altitude=400)

# Stay in Abuja overnight
all_points += stationary(ABUJA_CENTER,
                         trip_start_day.replace(hour=10, minute=30),
                         duration_minutes=20 * 60,
                         point_every_minutes=20, altitude=400, battery=60)

# Abuja -> Lagos flight (sparse points - airplane)
flight_day = trip_start_day + timedelta(days=1)
flight_start = flight_day.replace(hour=8, minute=0)
flight_points_locs = interpolate(ABUJA_CENTER, LAGOS_VI, 8)
for i, loc in enumerate(flight_points_locs):
    ts = flight_start + timedelta(minutes=i * 8)
    # Cruising altitude, high speed, low accuracy (airplane GPS quirks)
    all_points.append(make_point(
        loc[0], loc[1], ts,
        speed_kmh=750, accuracy=80, altitude=11000, battery=50,
    ))

# In Lagos: 2 days at Victoria Island
all_points += stationary(LAGOS_VI,
                         flight_day.replace(hour=10, minute=0),
                         duration_minutes=2 * 24 * 60,
                         point_every_minutes=30, altitude=10, battery=55)

# Return flight Lagos -> Abuja
return_flight_day = flight_day + timedelta(days=2)
return_start = return_flight_day.replace(hour=14, minute=0)
return_locs = interpolate(LAGOS_VI, ABUJA_CENTER, 8)
for i, loc in enumerate(return_locs):
    ts = return_start + timedelta(minutes=i * 8)
    all_points.append(make_point(
        loc[0], loc[1], ts,
        speed_kmh=750, accuracy=80, altitude=11000, battery=45,
    ))

# Drive Abuja -> Jos
all_points += trip(ABUJA_CENTER, HOME,
                   return_flight_day.replace(hour=16, minute=30),
                   duration_minutes=240, n_points=80,
                   speed_kmh=70, altitude=400, battery_start=40)

# --- Trip to Calabar (a few days later, drive south-east) ---
# This is to test that your bounds/zoom logic handles widely separated clusters
calabar_day = base_date + timedelta(days=18)
# Long drive ~700km, ~10 hours - represented as a sparse path
all_points += trip(HOME, CALABAR_CENTER,
                   calabar_day.replace(hour=5, minute=0),
                   duration_minutes=600, n_points=120,
                   speed_kmh=70, altitude=200)

# In Calabar 2 nights
all_points += stationary(CALABAR_CENTER,
                         calabar_day.replace(hour=15, minute=0),
                         duration_minutes=2 * 24 * 60,
                         point_every_minutes=45, altitude=30, battery=60)

# Drive back
return_day = calabar_day + timedelta(days=2)
all_points += trip(CALABAR_CENTER, HOME,
                   return_day.replace(hour=15, minute=0),
                   duration_minutes=600, n_points=120,
                   speed_kmh=70, altitude=200, battery_start=70)

# --- One GPS outlier (a bad fix) - useful for testing outlier handling ---
glitch_time = (base_date + timedelta(days=3)).replace(hour=14, minute=23)
all_points.append(make_point(
    9.5, 8.5,  # ~50km from anywhere real
    glitch_time, speed_kmh=0, accuracy=200, altitude=1500, battery=65,
))

# Sort by timestamp (your DB will return them this way)
all_points.sort(key=lambda p: p["timestamp"])

# Add an id field after sorting
for i, p in enumerate(all_points):
    p["id"] = i + 1

# -----------------------------------------------------------------------------
# Write outputs
# -----------------------------------------------------------------------------

with open("/home/claude/points.json", "w") as f:
    json.dump(all_points, f, indent=2)

# Build a GeoJSON FeatureCollection - this is what Mapbox GL JS wants
features = []
for p in all_points:
    features.append({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [p["longitude"], p["latitude"]],  # GeoJSON is lon,lat
        },
        "properties": {
            "id": p["id"],
            "timestamp": p["timestamp"],
            "speed": p["speed"],
            "accuracy": p["accuracy"],
            "altitude": p["altitude"],
            "battery": p["battery"],
            "bearing": p["bearing"],
        },
    })

geojson = {"type": "FeatureCollection", "features": features}

with open("/home/claude/points.geojson", "w") as f:
    json.dump(geojson, f, indent=2)

print(f"Generated {len(all_points)} points")
print(f"Time range: {all_points[0]['timestamp']} -> {all_points[-1]['timestamp']}")
