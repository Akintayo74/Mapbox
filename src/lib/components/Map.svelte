<script>
	import { onMount } from 'svelte';
	import { PUBLIC_MAPBOX_TOKEN } from '$env/static/public';

	const STYLE_URL = 'mapbox://styles/akintayo74/cmopgqyuk002k01qu0azpdp1q';
	const SOURCE_ID = 'points';
	const LAYER_ID = 'points-circle';

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

		map.addSource(SOURCE_ID, { type: 'geojson', data });
		map.addLayer({ id: LAYER_ID, type: 'circle', source: SOURCE_ID });

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
