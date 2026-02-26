from fastapi import FastAPI

from .app import create_championship, create_races
from .database import create_db_and_tables
from .f1_data import fetch_constructor_driver_pairs, fetch_races

YEAR = 2026


app = FastAPI()


@app.get("/")
def read_root():
    return {"Project": "F1 Race Analytics"}


def main():
    create_db_and_tables()
    races_data = fetch_races(YEAR)
    constructor_driver_pairs = fetch_constructor_driver_pairs(YEAR)
    create_races(YEAR, races_data)
    create_championship(YEAR, constructor_driver_pairs)


if __name__ == "__main__":
    main()
