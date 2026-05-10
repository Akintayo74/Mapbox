import { json } from '@sveltejs/kit';
import { neon } from '@neondatabase/serverless';
import { DATABASE_URL, TRACK_AUTH_TOKEN } from '$env/static/private';

const sql = neon(DATABASE_URL);

export async function POST({ request }) {
	const auth = request.headers.get('authorization') ?? '';
	if (auth !== `Bearer ${TRACK_AUTH_TOKEN}`) {
		return json({ error: 'Unauthorized' }, { status: 401 });
	}

	let body;
	try {
		body = await request.json();
	} catch {
		return json({ error: 'Invalid JSON' }, { status: 400 });
	}

	const { lat, lon, tst, acc, vel, bear, alt, batt } = body;

	if (lat == null || lon == null || tst == null) {
		return json({ error: 'Missing required fields: lat, lon, tst' }, { status: 400 });
	}

	await sql`
		INSERT INTO points (latitude, longitude, recorded_at, accuracy, speed, bearing, altitude, battery)
		VALUES (
			${lat},
			${lon},
			${new Date(tst * 1000).toISOString()},
			${acc ?? null},
			${vel ?? null},
			${bear ?? null},
			${alt ?? null},
			${batt ?? null}
		)
	`;

	return json({ ok: true }, { status: 201 });
}

// Health check — Colota pings GET before sending data
export async function GET() {
	return json({ ok: true });
}
