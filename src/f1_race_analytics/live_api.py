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
        f"<tr style='{'background: rgba(0,255,0,0.08);' if p.change > 0 else 'background: rgba(255,0,0,0.08);' if p.change < 0 else ''}'>"
        f"<td style='padding: .5rem 1rem; border-bottom: 1px solid var(--border);'>{p.position}</td>"
        f"<td style='padding: .5rem 1rem; border-bottom: 1px solid var(--border);'>{p.driver_name}</td>"
        f"<td style='padding: .5rem 1rem; border-bottom: 1px solid var(--border);'>#{p.driver_number}</td>"
        f"<td style='padding: .5rem 1rem; border-bottom: 1px solid var(--border); color: {'green' if p.cumulative_change > 0 else 'red' if p.cumulative_change < 0 else 'var(--muted)'};'>"
        f"{'&#9650; +' + str(p.cumulative_change) if p.cumulative_change > 0 else '&#9660; ' + str(p.cumulative_change) if p.cumulative_change < 0 else '&mdash;'}"
        f"</td>"
        f"</tr>"
        for p in positions
    )
    header_style = "text-align:left; padding: .5rem 1rem; color: var(--muted); font-family: 'Barlow Condensed', sans-serif; letter-spacing: 2px; text-transform: uppercase; border-bottom: 1px solid var(--border);"
    return (
        f'<div id="positions">'
        f"<table style='width:100%; border-collapse: collapse;'>"
        f"<thead><tr>"
        f"<th style='{header_style}'>Pos</th>"
        f"<th style='{header_style}'>Driver</th>"
        f"<th style='{header_style}'>No.</th>"
        f"<th style='{header_style}'>+/-</th>"
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
