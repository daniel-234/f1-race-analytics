import asyncio
from pathlib import Path

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.fastapi import DatastarResponse
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from .datasources import RaceDataSource, get_data_source

app = FastAPI(title="F1 Live Dashboard")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

origins = [
    "http://127.0.0.1:8000",  # or whatever was printed — likely this instead of localhost
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_race_data_source() -> RaceDataSource:
    return get_data_source()


def render_positions(positions) -> str:
    rows = "".join(
        f"<tr><td>P{p.position}</td><td>{p.driver_name}</td><td>#{p.driver_number}</td></tr>"
        for p in positions
    )
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
    datastar: str = None,
    data_source: RaceDataSource = Depends(get_race_data_source),
):
    async def stream():
        while True:
            # Stop when the client navigates away
            if await request.is_disconnected():
                break
            positions = await data_source.get_positions(fixture_id)
            yield SSE.patch_elements(render_positions(positions))

            # stop when race ends
            if data_source.is_finished():
                break

            await asyncio.sleep(3)

    return DatastarResponse(stream())
