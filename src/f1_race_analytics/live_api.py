import asyncio
from pathlib import Path

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.fastapi import DatastarResponse
from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates

from .datasources import RaceDataSource, get_data_source

app = FastAPI(title="F1 Live Dashboard")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_race_data_source() -> RaceDataSource:
    return get_data_source()


def render_positions(positions) -> str:
    rows = "".join(
        f"<tr><td>P{p.position}</td><td>{p.driver_name}</td><td>#{p.driver_number}</td></tr>"
        for p in positions
    )
    print(rows)
    return (
        f'<div id="positions" class="panel">'
        f"<h2>Positions</h2>"
        f"<table>"
        f"<tr><th>Pos</th><th>Driver</th><th>No.</th></tr>"
        f"{rows}"
        f"</table>"
        f"</div>"
    )


@app.get("/live/stream")
async def live_endpoint(
    request: Request,
    fixture_id: str,
    data_source: RaceDataSource = Depends(get_race_data_source),
):
    async def stream():
        while True:
            positions = await data_source.get_positions(fixture_id)
            yield SSE.patch_elements(render_positions(positions))
            # Change it to 15 to resemble the API update time
            await asyncio.sleep(3)

    return DatastarResponse(stream())


@app.get("/replay")
async def replay_page(request: Request):
    return templates.TemplateResponse("replay_dashboard.html", {"request": request})
