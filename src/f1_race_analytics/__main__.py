from fastapi import Depends, FastAPI
from sqlmodel import Session

from .app import create_championship, create_races
from .database import create_db_and_tables, get_session
from .f1_data import fetch_constructor_driver_pairs, fetch_races

YEAR = 2026


app = FastAPI()


@app.get("/races")
def list_races(*, session: Session = Depends(get_session)):
    create_db_and_tables()
    races_data = fetch_races(YEAR)
    championship = create_races(2026, races_data)
    return championship.races


def main():
    create_db_and_tables()
    races_data = fetch_races(YEAR)
    constructor_driver_pairs = fetch_constructor_driver_pairs(YEAR)
    create_races(YEAR, races_data)
    create_championship(YEAR, constructor_driver_pairs)


if __name__ == "__main__":
    main()
