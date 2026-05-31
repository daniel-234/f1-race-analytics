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
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


def get_race_data_source() -> RaceDataSource:
    return get_data_source()


def _row_class(change: int) -> str:
    if change > 0:
        return ' class="row-up"'
    if change < 0:
        return ' class="row-down"'
    return ""


def _delta_class(cumulative_change: int) -> str:
    if cumulative_change > 0:
        return "delta-up"
    if cumulative_change < 0:
        return "delta-down"
    return "delta-flat"


def render_positions(positions) -> str:
    rows = "".join(
        f'<tr{_row_class(p.change)}>'
        f'<td>{p.position}</td>'
        f'<td>{p.driver_name}</td>'
        f'<td>#{p.driver_number}</td>'
        f'<td class="{_delta_class(p.cumulative_change)}">'
        f'{"&#9650; +" + str(p.cumulative_change) if p.cumulative_change > 0 else "&#9660; " + str(p.cumulative_change) if p.cumulative_change < 0 else "&mdash;"}'
        f'</td>'
        f'</tr>'
        for p in positions
    )

    return (
        f'<div id="positions">'
        f'<table class="data-table">'
        f"<thead><tr>"
        f"<th>Pos</th>"
        f"<th>Driver</th>"
        f"<th>No.</th>"
        f"<th>+/-</th>"
        f"</tr></thead>"
        f"<tbody>{rows}</tbody>"
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
