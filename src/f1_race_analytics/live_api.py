import asyncio
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

import httpx
import uvicorn
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.fastapi import DatastarResponse
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="F1 Live Dashboard")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

OPENF1_API = "https://api.openf1.org/v1"


@dataclass
class DriverStanding:
    position: int
    change: int


def render_positions(
    standings: dict[int, DriverStanding], drivers: dict[int, str]
) -> str:
    """
    Render the drivers positions table body as HTML
    """
    rows = []
    table_rows = []
    for driver_number, standing in standings.items():
        rows.append((driver_number, standing.position, standing.change))
    for row in sorted(rows, key=lambda x: x[1])[:10]:
        number, position, change = row
        arrow = "▲" if change < 0 else "▼" if change > 0 else ""
        tr = f"<tr><td>P{position}</td><td>{number}</td><td>{arrow} {abs(change)}</td></tr>"
        table_rows.append(tr)

    return f'<div id="positions" class="panel"><h2>Positions</h2><table><tr><th>Pos</th><th>Driver</th></tr>{"\n".join(table_rows)}</table></div>'


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="index.html", context={"title": "F1 Analytics Platform"}
    )


@app.get("/replay")
async def replay_page(request: Request):
    """Serve the HTML page for replay."""
    return templates.TemplateResponse(
        "live_dashboard.html",
        {
            "request": request,
        },
    )


@app.get("/replay/stream")
async def replay_session(session_key: str = "9839", speed: float = 1):
    """Stream replay data via SSE."""

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

        standings: dict[int, DriverStanding] = {}
        count = 0

        for timestamp, group in grouped:
            count += 1
            if count > 50:
                break

            for p in group:
                driver, pos = p.get("driver_number"), p.get("position")
                if driver and pos:
                    # Store the drivers' previous standings to compare them with
                    # the new positions and check if there has been a change
                    previous_position = (
                        pos if count == 1 else standings[driver].position
                    )
                    new_position = pos
                    change = new_position - previous_position
                    standings[driver] = DriverStanding(
                        position=new_position, change=change
                    )

            yield SSE.patch_elements(render_positions(standings, drivers))

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
