from sqlmodel import Session, select

from .database import create_db_and_tables, engine
from .models import Championship, Race, Constructor
from .f1_data import Event, ConstructorData


def create_races(year: int, races_data: list[Event]) -> Championship:
    """
    Create the chanpionship and races instances for the given year
    """
    with Session(engine) as session:
        championship = Championship(year=year)

        races = [Race(name=race.name, championship=championship) for race in races_data]

        session.add_all(races)
        session.commit()
        for race in races:
            session.refresh(race)

        print("\n\nChampionship's races: ", championship.races)
        
        return championship

        
def create_constructors(year: int, constructors_data: list[ConstructorData]) -> Championship:
    """
    Create the Constructor instances for the given year
    """
    with Session(engine) as session:
        championship = Championship(year=year)

        constructors = [Constructor(name=constructor.name, nationality=constructor.nationality, championship=championship) for constructor in constructors_data]

        session.add_all(constructors)
        session.commit()
        for constructor in constructors:
            session.refresh(constructor)

        print("\n\nConstructors: ", championship.constructors)

        return championship