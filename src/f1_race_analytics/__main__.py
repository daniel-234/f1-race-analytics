from .database import create_db_and_tables
from .app import create_races


def main():
    create_db_and_tables()
    create_races()


if __name__ == '__main__':
    main()