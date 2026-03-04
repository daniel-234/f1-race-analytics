from .database import (
    clear_db_and_tables,
    create_championship,
    create_db_and_tables,
    create_races,
    create_results,
)
from .f1_data import fetch_constructor_driver_pairs, fetch_races, fetch_results_by_race

YEAR = 2025


def main():
    clear_db_and_tables()
    create_db_and_tables()
    races_data = fetch_races(YEAR)
    constructor_driver_pairs = fetch_constructor_driver_pairs(YEAR)
    create_races(YEAR, races_data)
    create_championship(YEAR, constructor_driver_pairs)
    result_data = fetch_results_by_race(2025, "monza")
    c = create_results(YEAR, result_data)
    print(c)


if __name__ == "__main__":
    main()
