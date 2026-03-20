from collections.abc import AsyncGenerator
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
    create_championship,
    create_db_and_tables,
    create_race_results,
    create_races,
    get_all_races,
    get_driver_ranks,
    get_result_by_circuit_id,
    get_session,
)
from .f1_data import (
    EventStatus,
    fetch_constructor_driver_pairs,
    fetch_races,
    fetch_results_by_race,
)

YEAR = 2026


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    clear_db_and_tables()
    create_db_and_tables()
    races_data = fetch_races(YEAR)
    create_races(YEAR, races_data)
    constructor_driver_pairs = fetch_constructor_driver_pairs(YEAR)
    create_championship(YEAR, constructor_driver_pairs)
    for race in races_data:
        if race.status() == EventStatus.PAST:
            result_data = fetch_results_by_race(YEAR, race.circuit_id)
            if result_data:
                create_race_results(YEAR, result_data)
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


@app.get("/results/{circuit_id}", response_class=HTMLResponse)
async def get_race_result(
    circuit_id: str, request: Request, session: Annotated[Session, Depends(get_session)]
) -> HTMLResponse:
    results = get_result_by_circuit_id(session, circuit_id)
    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={"results": results, "circuit_id": circuit_id},
    )


@app.get("/replay")
async def replay_page(request: Request):
    return templates.TemplateResponse(
        "replay_dashboard.html",
        {
            "request": request,
            "replay_url": "http://localhost:8001",
        },
    )


@app.get("/standings/drivers", response_class=HTMLResponse)
async def get_drivers_standings(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> HTMLResponse:
    standings = get_driver_ranks(session, YEAR)
    return templates.TemplateResponse(
        request=request,
        name="drivers_standings.html",
        context={"standings": standings, "year": YEAR},
    )
