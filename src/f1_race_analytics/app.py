from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlmodel import Session

from .database import (
    create_db_and_tables,
    create_races,
    get_all_races,
    get_race_by_circuit_id,
    get_result_by_circuit_id,
    get_session,
)
from .f1_data import fetch_races
from .models import Race, RaceResult

YEAR = 2025


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """ "
    Create tables; fetch and create races
    """
    create_db_and_tables()
    races_data = fetch_races(2026)
    create_races(2026, races_data)
    # circuit = fetch_results_by_race(YEAR, "monza")
    # create_results(YEAR, circuit)
    yield


app = FastAPI(title="F1 Race Analytics API", lifespan=lifespan)


def populate_db():
    create_db_and_tables()
    races_data = fetch_races(2026)
    create_races(2026, races_data)


@app.get("/races")
def list_races(session: Annotated[Session, Depends(get_session)]) -> Sequence[Race]:
    return get_all_races(session)


@app.get("/races/{circuit_id}")
def get_race(
    circuit_id: str, session: Annotated[Session, Depends(get_session)]
) -> Race | None:
    return get_race_by_circuit_id(session, circuit_id)


@app.get("/results/{circuit_id}")
def get_race_result(
    circuit_id: str, session: Annotated[Session, Depends(get_session)]
) -> list[RaceResult] | None:
    return get_result_by_circuit_id(session, circuit_id)
