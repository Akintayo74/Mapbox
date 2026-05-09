<script>
	let { value, counts, onChange } = $props();

	let open = $state(false);
	let viewMonth = $state({ year: 2000, month: 0 });
	let focusKey = $state('');
	let rootEl;

	const WEEKDAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

	const maxCount = $derived(Math.max(1, ...counts.values()));

	const monthLabel = $derived(
		new Date(viewMonth.year, viewMonth.month, 1).toLocaleDateString('en-US', {
			month: 'long',
			year: 'numeric'
		})
	);

	const pillLabel = $derived.by(() => {
		const { year, month, day } = parseKey(value);
		const d = new Date(year, month, day);
		return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
	});

	const grid = $derived.by(() => {
		const { year, month } = viewMonth;
		const firstWeekday = new Date(year, month, 1).getDay();
		const daysInMonth = new Date(year, month + 1, 0).getDate();
		const cells = [];
		for (let i = 0; i < firstWeekday; i++) cells.push(null);
		for (let d = 1; d <= daysInMonth; d++) {
			const key = dateKey(year, month, d);
			cells.push({ day: d, key, count: counts.get(key) ?? 0 });
		}
		while (cells.length % 7 !== 0) cells.push(null);
		return cells;
	});

	function dateKey(year, month, day) {
		return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
	}

	function parseKey(key) {
		const [y, m, d] = key.split('-').map(Number);
		return { year: y, month: m - 1, day: d };
	}

	function shiftMonth(delta) {
		const m = viewMonth.month + delta;
		viewMonth = {
			year: viewMonth.year + Math.floor(m / 12),
			month: ((m % 12) + 12) % 12
		};
	}

	function selectDay(key) {
		onChange(key);
		open = false;
	}

	function openCalendar() {
		viewMonth = parseKey(value);
		focusKey = value;
		open = true;
	}

	function shiftFocus(deltaDays) {
		const { year, month, day } = parseKey(focusKey);
		const next = new Date(year, month, day + deltaDays);
		const nextKey = dateKey(next.getFullYear(), next.getMonth(), next.getDate());
		focusKey = nextKey;
		const fk = parseKey(nextKey);
		if (fk.year !== viewMonth.year || fk.month !== viewMonth.month) {
			viewMonth = { year: fk.year, month: fk.month };
		}
	}

	function handleKey(e) {
		if (!open) return;
		if (e.key === 'Escape') {
			open = false;
			e.preventDefault();
		} else if (e.key === 'ArrowLeft') {
			shiftFocus(-1);
			e.preventDefault();
		} else if (e.key === 'ArrowRight') {
			shiftFocus(1);
			e.preventDefault();
		} else if (e.key === 'ArrowUp') {
			shiftFocus(-7);
			e.preventDefault();
		} else if (e.key === 'ArrowDown') {
			shiftFocus(7);
			e.preventDefault();
		} else if (e.key === 'Enter') {
			selectDay(focusKey);
			e.preventDefault();
		}
	}

	function handleDocClick(e) {
		if (!open) return;
		if (rootEl && !rootEl.contains(e.target)) open = false;
	}

	$effect(() => {
		document.addEventListener('mousedown', handleDocClick);
		document.addEventListener('keydown', handleKey);
		return () => {
			document.removeEventListener('mousedown', handleDocClick);
			document.removeEventListener('keydown', handleKey);
		};
	});
</script>

<div class="root" bind:this={rootEl}>
	<button class="pill" onclick={() => (open ? (open = false) : openCalendar())}>
		<span class="pill-dot"></span>
		<span class="pill-label">{pillLabel}</span>
	</button>

	{#if open}
		<div class="overlay" role="dialog" aria-label="Date picker">
			<div class="header">
				<button class="nav" onclick={() => shiftMonth(-1)} aria-label="Previous month">‹</button>
				<span class="month">{monthLabel}</span>
				<button class="nav" onclick={() => shiftMonth(1)} aria-label="Next month">›</button>
			</div>
			<div class="weekdays">
				{#each WEEKDAYS as w, i}
					<span class="weekday" aria-hidden="true">{w}</span>
				{/each}
			</div>
			<div class="grid" role="grid">
				{#each grid as cell}
					{#if cell === null}
						<span class="cell empty"></span>
					{:else}
						{@const tint = cell.count / maxCount}
						{@const selected = cell.key === value}
						{@const focused = cell.key === focusKey}
						<button
							class="cell"
							class:selected
							class:focused
							class:has-data={cell.count > 0}
							style="--tint: {tint};"
							onclick={() => selectDay(cell.key)}
							aria-label={`${cell.key}, ${cell.count} points`}
						>
							<span class="day-num">{cell.day}</span>
						</button>
					{/if}
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.root {
		position: absolute;
		top: 16px;
		left: 16px;
		z-index: 10;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}

	.pill {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding: 8px 14px;
		background: rgba(255, 255, 255, 0.96);
		border: 1px solid rgba(0, 0, 0, 0.08);
		border-radius: 999px;
		font-size: 13px;
		font-weight: 500;
		color: #1a1a1a;
		cursor: pointer;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
		transition: box-shadow 120ms ease, transform 80ms ease;
	}
	.pill:hover {
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.1);
	}
	.pill:active {
		transform: translateY(1px);
	}

	.pill-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: #c45a3d;
	}

	.overlay {
		position: absolute;
		top: calc(100% + 6px);
		left: 0;
		width: 252px;
		padding: 12px;
		background: rgba(255, 255, 255, 0.98);
		border: 1px solid rgba(0, 0, 0, 0.08);
		border-radius: 12px;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
		font-size: 12px;
		color: #1a1a1a;
		backdrop-filter: blur(6px);
	}

	.header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 8px;
	}
	.nav {
		width: 24px;
		height: 24px;
		border: none;
		background: transparent;
		border-radius: 6px;
		font-size: 16px;
		line-height: 1;
		color: #555;
		cursor: pointer;
	}
	.nav:hover {
		background: rgba(0, 0, 0, 0.04);
	}
	.month {
		font-weight: 600;
		font-size: 13px;
	}

	.weekdays {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		margin-bottom: 4px;
	}
	.weekday {
		display: flex;
		justify-content: center;
		font-size: 10px;
		font-weight: 500;
		color: #999;
		letter-spacing: 0.04em;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 2px;
	}
	.cell {
		position: relative;
		aspect-ratio: 1 / 1;
		border: none;
		background: transparent;
		border-radius: 6px;
		font-size: 12px;
		color: #1a1a1a;
		cursor: pointer;
		padding: 0;
	}
	.cell.empty {
		cursor: default;
	}
	.cell.has-data::before {
		content: '';
		position: absolute;
		inset: 2px;
		border-radius: 5px;
		background: rgba(196, 90, 61, 0.18);
		opacity: var(--tint);
	}
	.cell:hover:not(.empty) {
		background: rgba(0, 0, 0, 0.04);
	}
	.cell.focused {
		outline: 1.5px solid rgba(196, 90, 61, 0.4);
		outline-offset: -1px;
	}
	.cell.selected {
		background: #c45a3d;
		color: white;
	}
	.cell.selected::before {
		display: none;
	}
	.day-num {
		position: relative;
		z-index: 1;
	}
</style>
