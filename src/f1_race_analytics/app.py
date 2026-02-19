from sqlmodel import Session

from .database import create_db_and_tables, engine
from .models import Championship, Race
from .f1_data import fetch_data


def create_races():
    with Session(engine) as session:
        championship_2026 = Championship(year=2026)

        races_data = fetch_data()
        races = [Race(name=race.name, championship_id=championship_2026.id) for race in races_data]

        session.add(races)
        session.commit()

        session.refresh(races)

        print("Championship's races: ", championship_2026.races)