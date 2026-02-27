from fastapi import Depends, FastAPI
from sqlmodel import Session

from .database import create_db_and_tables, create_races, get_session
from .f1_data import fetch_races

app = FastAPI()


@app.get("/races")
def list_races(*, session: Session = Depends(get_session)):
    create_db_and_tables()
    races_data = fetch_races(2026)
    championship = create_races(2026, races_data)
    return championship.races
