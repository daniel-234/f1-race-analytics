import uvicorn

from .app import YEAR
from .database import (
    clear_db_and_tables,
    create_championship,
    create_db_and_tables,
    create_race_results,
    create_races,
)
from .f1_data import fetch_constructor_driver_pairs, fetch_races, fetch_results_by_race

CIRCUIT_ID = "monza"


def main():
    clear_db_and_tables()
    create_db_and_tables()
    races_data = fetch_races(YEAR)
    create_races(YEAR, races_data)
    constructor_driver_pairs = fetch_constructor_driver_pairs(YEAR)
    create_championship(YEAR, constructor_driver_pairs)
    result_data = fetch_results_by_race(YEAR, CIRCUIT_ID)
    create_race_results(YEAR, result_data)


def dev():
    uvicorn.run("f1_race_analytics.app:app", reload=True)


def live():
    uvicorn.run(
        "f1_race_analytics.live_api:app",
        reload=True,
        port=8001,
    )


if __name__ == "__main__":
    main()
