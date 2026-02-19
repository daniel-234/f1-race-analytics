from sqlmodel import Session

from .database import create_db_and_tables, engine
from .models import Championship, Race
from .f1_data import fetch_data


def create_races():
    with Session(engine) as session:
        championship_2026 = Championship(year=2026)

        races_data = fetch_data()
        races = [Race(name=race.name, championship=championship_2026) for race in races_data]

        session.add_all(races)
        session.commit()

        for race in races:
            session.refresh(race)

        print("\nChampionship's races: ", championship_2026.races)