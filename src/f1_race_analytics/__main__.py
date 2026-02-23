from .database import create_db_and_tables
from .app import create_races, create_championship      
from .f1_data import fetch_races, fetch_constructors, fetch_constructor_driver_pairs

YEAR = 2026


def main():
    create_db_and_tables()
    races_data = fetch_races(YEAR)
    constructors_data = fetch_constructors(YEAR)
    constructor_driver_pairs = fetch_constructor_driver_pairs(YEAR)
    create_races(YEAR, races_data)
    create_championship(YEAR, constructor_driver_pairs) 
    

if __name__ == '__main__':
    main()