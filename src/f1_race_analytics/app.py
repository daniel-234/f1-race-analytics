from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlmodel import Session

from .database import (
    create_db_and_tables,
    create_races,
    get_all_races,
    get_race_by_circuit_id,
    get_session,
)
from .f1_data import fetch_races
from .models import Race

app = FastAPI()


def populate_db():
    create_db_and_tables()
    races_data = fetch_races(2026)
    create_races(2026, races_data)


@app.get("/races")
def list_races(session: Annotated[Session, Depends(get_session)]) -> Sequence[Race]:
    populate_db()
    return get_all_races(session)


@app.get("/races/{circuit_id}")
def get_race(
    circuit_id: str, session: Annotated[Session, Depends(get_session)]
) -> Race | None:
    populate_db()
    return get_race_by_circuit_id(session, circuit_id)
