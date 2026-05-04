<script>
	import { onMount } from 'svelte';
	import { PUBLIC_MAPBOX_TOKEN } from '$env/static/public';

	const STYLE_URL = 'mapbox://styles/akintayo74/cmopgqyuk002k01qu0azpdp1q';
	const POINTS_SOURCE_ID = 'points';
	const HEATMAP_LAYER_ID = 'points-heatmap';

	let container;
	let map;

	onMount(async () => {
		const mapboxgl = (await import('mapbox-gl')).default;
		mapboxgl.accessToken = PUBLIC_MAPBOX_TOKEN;

		map = new mapboxgl.Map({
			container,
			style: STYLE_URL
		});

		const [data] = await Promise.all([
			fetch('/points.geojson').then((r) => r.json()),
			new Promise((resolve) => map.on('load', resolve))
		]);

		const buckets = new Map();
		for (const f of data.features) {
			const [lng, lat] = f.geometry.coordinates;
			const key = `${lng.toFixed(5)},${lat.toFixed(5)}`;
			const bucket = buckets.get(key);
			if (bucket) {
				bucket.count++;
			} else {
				buckets.set(key, {
					coords: [Number(lng.toFixed(5)), Number(lat.toFixed(5))],
					count: 1
				});
			}
		}
		const maxCount = Math.max(...Array.from(buckets.values(), (b) => b.count));
		const weighted = {
			type: 'FeatureCollection',
			features: Array.from(buckets.values(), ({ coords, count }) => ({
				type: 'Feature',
				geometry: { type: 'Point', coordinates: coords },
				properties: { weight: (count / maxCount) ** 3 }
			}))
		};

		map.addSource(POINTS_SOURCE_ID, { type: 'geojson', data: weighted });
		map.addLayer({
			id: HEATMAP_LAYER_ID,
			type: 'heatmap',
			source: POINTS_SOURCE_ID,
			paint: {
				'heatmap-weight': ['get', 'weight'],
				'heatmap-radius': [
					'interpolate',
					['linear'],
					['zoom'],
					10, 22,
					14, 12,
					17, 5
				],
				'heatmap-intensity': 1,
				'heatmap-color': [
					'interpolate',
					['linear'],
					['heatmap-density'],
					0,    'rgba(0,0,0,0)',
					0.2,  '#d4c5e0',
					0.4,  '#9c7bbf',
					0.6,  '#5e3f96',
					0.8,  '#261b5c',
					1,    '#0a0626'
				],
				'heatmap-opacity': 1
			}
		});

		const bounds = data.features.reduce(
			(b, f) => b.extend(f.geometry.coordinates),
			new mapboxgl.LngLatBounds(
				data.features[0].geometry.coordinates,
				data.features[0].geometry.coordinates
			)
		);
		map.fitBounds(bounds, { padding: 48, animate: false });

		return () => map?.remove();
	});
</script>

<div bind:this={container} class="map"></div>

<style>
	.map {
		position: absolute;
		inset: 0;
	}
</style>
