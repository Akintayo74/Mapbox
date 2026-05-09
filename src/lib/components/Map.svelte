<script>
	import { onMount } from 'svelte';
	import { PUBLIC_MAPBOX_TOKEN } from '$env/static/public';
	import CalendarPill from './CalendarPill.svelte';

	const STYLE_URL = 'mapbox://styles/akintayo74/cmopgqyuk002k01qu0azpdp1q';
	const ROUTE_COLOR = '#c45a3d';

	let container;
	let map;
	let mapReady = $state(false);
	let firstRender = true;

	const pointsByDate = new Map();
	let counts = $state(new Map());
	let selectedDate = $state(null);

	onMount(async () => {
		const mapboxgl = (await import('mapbox-gl')).default;
		mapboxgl.accessToken = PUBLIC_MAPBOX_TOKEN;

		map = new mapboxgl.Map({ container, style: STYLE_URL });

		const [data] = await Promise.all([
			fetch('/points.geojson').then((r) => r.json()),
			new Promise((resolve) => map.on('load', resolve))
		]);

		for (const f of data.features) {
			const key = f.properties.timestamp.slice(0, 10);
			let arr = pointsByDate.get(key);
			if (!arr) {
				arr = [];
				pointsByDate.set(key, arr);
			}
			arr.push(f);
		}
		for (const arr of pointsByDate.values()) {
			arr.sort((a, b) => a.properties.timestamp.localeCompare(b.properties.timestamp));
		}

		const nextCounts = new Map();
		for (const [k, v] of pointsByDate) nextCounts.set(k, v.length);
		counts = nextCounts;

		let bestKey = null;
		let bestCount = 0;
		for (const [k, v] of pointsByDate) {
			if (v.length > bestCount) {
				bestCount = v.length;
				bestKey = k;
			}
		}

		const empty = { type: 'FeatureCollection', features: [] };
		map.addSource('day-route', { type: 'geojson', data: empty });
		map.addSource('day-endpoints', { type: 'geojson', data: empty });

		map.addLayer({
			id: 'day-route-shadow',
			type: 'line',
			source: 'day-route',
			layout: { 'line-cap': 'round', 'line-join': 'round' },
			paint: {
				'line-color': ROUTE_COLOR,
				'line-width': 8,
				'line-opacity': 0.18
			}
		});
		map.addLayer({
			id: 'day-route-line',
			type: 'line',
			source: 'day-route',
			layout: { 'line-cap': 'round', 'line-join': 'round' },
			paint: {
				'line-color': ROUTE_COLOR,
				'line-width': 3,
				'line-opacity': 0.9
			}
		});
		map.addLayer({
			id: 'day-endpoint-end',
			type: 'circle',
			source: 'day-endpoints',
			filter: ['==', ['get', 'role'], 'end'],
			paint: {
				'circle-radius': 6,
				'circle-color': '#ffffff',
				'circle-stroke-color': ROUTE_COLOR,
				'circle-stroke-width': 2.5
			}
		});
		map.addLayer({
			id: 'day-endpoint-start',
			type: 'circle',
			source: 'day-endpoints',
			filter: ['==', ['get', 'role'], 'start'],
			paint: {
				'circle-radius': 5,
				'circle-color': ROUTE_COLOR,
				'circle-stroke-color': '#ffffff',
				'circle-stroke-width': 1.5
			}
		});

		mapReady = true;
		selectedDate = bestKey;

		return () => map?.remove();
	});

	$effect(() => {
		if (!mapReady || !selectedDate) return;
		renderDay(selectedDate);
	});

	function renderDay(dateKey) {
		const pts = pointsByDate.get(dateKey);
		const empty = { type: 'FeatureCollection', features: [] };
		if (!pts || pts.length === 0) {
			map.getSource('day-route').setData(empty);
			map.getSource('day-endpoints').setData(empty);
			return;
		}

		const coords = pts.map((p) => p.geometry.coordinates);

		const route = {
			type: 'FeatureCollection',
			features: [
				{
					type: 'Feature',
					geometry: { type: 'LineString', coordinates: coords },
					properties: {}
				}
			]
		};

		const endpoints = {
			type: 'FeatureCollection',
			features: [
				{
					type: 'Feature',
					geometry: { type: 'Point', coordinates: coords[0] },
					properties: { role: 'start' }
				}
			]
		};
		if (coords.length > 1) {
			endpoints.features.push({
				type: 'Feature',
				geometry: { type: 'Point', coordinates: coords[coords.length - 1] },
				properties: { role: 'end' }
			});
		}

		map.getSource('day-route').setData(route);
		map.getSource('day-endpoints').setData(endpoints);

		fitToCoords(coords, firstRender);
		firstRender = false;
	}

	function fitToCoords(coords, instant) {
		let minLng = Infinity,
			minLat = Infinity,
			maxLng = -Infinity,
			maxLat = -Infinity;
		for (const [lng, lat] of coords) {
			if (lng < minLng) minLng = lng;
			if (lng > maxLng) maxLng = lng;
			if (lat < minLat) minLat = lat;
			if (lat > maxLat) maxLat = lat;
		}
		map.fitBounds(
			[
				[minLng, minLat],
				[maxLng, maxLat]
			],
			{
				padding: 80,
				animate: !instant,
				duration: 600
			}
		);
	}
</script>

<div class="root">
	<div class="map" bind:this={container}></div>
	{#if mapReady && selectedDate}
		<CalendarPill
			value={selectedDate}
			{counts}
			onChange={(d) => (selectedDate = d)}
		/>
	{/if}
</div>

<style>
	.root {
		position: absolute;
		inset: 0;
	}
	.map {
		position: absolute;
		inset: 0;
	}
</style>
