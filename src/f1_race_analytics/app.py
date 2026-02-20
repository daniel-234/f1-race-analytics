from sqlmodel import Session, select

from .database import create_db_and_tables, engine
from .models import Championship, Race
from .f1_data import Event


def create_races(year: int, races_data: list[Event]) -> Championship:
    with Session(engine) as session:
        championship = Championship(year=year)

        races = [Race(name=race.name, championship=championship) for race in races_data]

        session.add_all(races)
        session.commit()
        for race in races:
            session.refresh(race)

        print("\n\nChampionship's races: ", championship.races)
        
        return championship

        