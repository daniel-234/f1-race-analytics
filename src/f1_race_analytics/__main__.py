from .database import create_db_and_tables
from .app import create_races
from .f1_data import fetch_data

YEAR = 2026


def main():
    create_db_and_tables()
    races_data = fetch_data(YEAR)
    create_races(YEAR, races_data)


if __name__ == '__main__':
    main()