from .database import create_db_and_tables
from .app import create_races, create_championship      
from .f1_data import fetch_races, fetch_constructors

YEAR = 2026


def main():
    create_db_and_tables()
    races_data = fetch_races(YEAR)
    constructors_data = fetch_constructors(YEAR)
    create_races(YEAR, races_data)
    create_championship(YEAR) 
    

if __name__ == '__main__':
    main()