import asyncio
from itertools import groupby

import httpx
import uvicorn
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.fastapi import DatastarResponse
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="F1 Live Dashboard")

OPENF1_API = "https://api.openf1.org/v1"

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>F1 Live Dashboard</title>
    <script type="module" src="https://cdn.jsdelivr.net/gh/starfederation/datastar@main/bundles/datastar.js"></script>
    <style>
        body { font-family: system-ui, sans-serif; padding: 2rem; max-width: 800px; margin: 0 auto; }
        button { padding: 0.5rem 1rem; margin: 0.25rem; cursor: pointer; }
        .panel { border: 1px solid #ddd; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { text-align: left; padding: 0.5rem; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <h1>F1 Live Dashboard</h1>
    <div>
        <button data-on:click="@get('/replay?session_key=9839')">
            Replay Abu Dhabi 2025
        </button>
        <button data-on:click="@get('/replay?session_key=latest')">
            Replay Latest Session
        </button>
    </div>
    <div id="session-info" class="panel">
        <p>Click a button to start</p>
    </div>
    <div id="positions" class="panel">
        <p>Position data will appear here</p>
    </div>
    <div id="status" class="panel" style="background: #f0fff0;">
        <p>Ready</p>
    </div>
</body>
</html>
"""


def build_positions_html(standings: dict[int, int], drivers: dict[int, str]) -> str:
    sorted_drivers = sorted(standings.items(), key=lambda x: x[1])
    rows = "".join(
        f"<tr><td>P{pos}</td><td>{drivers.get(num, f'#{num}')}</td></tr>"
        for num, pos in sorted_drivers[:10]
    )
    return f'<div id="positions" class="panel"><h2>Positions</h2><table><tr><th>Pos</th><th>Driver</th></tr>{rows}</table></div>'


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE


@app.get("/replay")
async def replay_session(session_key: str = "9839", speed: float = 1):
    """Replay historical position data as live stream."""

    async def stream():
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OPENF1_API}/sessions?session_key={session_key}")
            sessions = resp.json() if resp.status_code == 200 else []

            if sessions:
                s = sessions[0]
                yield SSE.patch_elements(
                    f'<div id="session-info" class="panel"><h2>{s.get("session_name")} - {s.get("location")}</h2></div>'
                )

            # Fetch driver names
            resp = await client.get(f"{OPENF1_API}/drivers?session_key={session_key}")
            driver_data = resp.json() if resp.status_code == 200 else []
            drivers = {
                d["driver_number"]: d.get("name_acronym", f"#{d['driver_number']}")
                for d in driver_data
            }

            resp = await client.get(f"{OPENF1_API}/position?session_key={session_key}")
            positions = resp.json() if resp.status_code == 200 else []

        if not positions:
            yield SSE.patch_elements(
                '<div id="status" class="panel"><p>No data found</p></div>'
            )
            return

        sorted_positions = sorted(positions, key=lambda x: x.get("date", ""))
        grouped = groupby(sorted_positions, key=lambda x: x.get("date", ""))

        standings: dict[int, int] = {}
        count = 0

        for timestamp, group in grouped:
            count += 1
            if count > 50:
                break

            for p in group:
                driver, pos = p.get("driver_number"), p.get("position")
                if driver and pos:
                    standings[driver] = pos

            yield SSE.patch_elements(build_positions_html(standings, drivers))

            time_short = timestamp[11:19] if len(timestamp) > 19 else timestamp
            yield SSE.patch_elements(
                f'<div id="status" class="panel" style="background: #f0fff0;"><p>Update {count} - {time_short}</p></div>'
            )

            await asyncio.sleep(speed)

        yield SSE.patch_elements(
            '<div id="status" class="panel" style="background: #f0fff0;"><p>Replay complete</p></div>'
        )

    return DatastarResponse(stream())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
