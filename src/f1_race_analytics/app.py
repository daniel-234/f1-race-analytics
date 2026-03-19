from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from .database import (
    clear_db_and_tables,
    create_db_and_tables,
    create_races,
    get_all_races,
    get_race_by_circuit_id,
    get_result_by_circuit_id,
    get_session,
)
from .f1_data import fetch_races
from .models import Race, RaceResult

YEAR = 2026


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """ "
    Create tables; fetch and create races
    """
    clear_db_and_tables()
    create_db_and_tables()
    races_data = fetch_races(YEAR)
    create_races(YEAR, races_data)
    yield


app = FastAPI(title="F1 Race Analytics API", lifespan=lifespan)
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def populate_db():
    create_db_and_tables()
    races_data = fetch_races(YEAR)
    create_races(YEAR, races_data)


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> HTMLResponse:
    races = get_all_races(session)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "2026 Season", "races": races, "replay_url": "/replay"},
    )


@app.get("/races/{circuit_id}")
def get_race(
    circuit_id: str, session: Annotated[Session, Depends(get_session)]
) -> Race | None:
    return get_race_by_circuit_id(session, circuit_id)


@app.get("/results/{circuit_id}")
def get_race_result(
    circuit_id: str, session: Annotated[Session, Depends(get_session)]
) -> Sequence[RaceResult] | None:
    return get_result_by_circuit_id(session, circuit_id)


@app.get("/replay")
async def replay_page(request: Request):
    return templates.TemplateResponse(
        "replay_dashboard.html",
        {
            "request": request,
            "replay_url": "http://localhost:8001",
        },
    )
