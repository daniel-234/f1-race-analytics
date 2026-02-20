from sqlmodel import Session, select

from .database import create_db_and_tables, engine
from .models import Championship, Race, Constructor, Driver
from .f1_data import Event, ConstructorData, DriverData


def create_races(year: int, races_data: list[Event]) -> Championship:
    """
    Create the chanpionship and races instances for the given year
    """
    with Session(engine) as session:
        championship = Championship(year=year)

        races = [Race(name=race.name, championship=championship) for race in races_data]

        session.add_all(races)
        session.commit()
        session.refresh(championship, attribute_names=["year", "races"])
        
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
        session.refresh(championship, attribute_names=["year", "constructors"])

    return championship


def create_drivers(year: int, drivers_data: list[DriverData]) -> Championship:
    """
    Create the Driver instances for the given year
    """
    with Session(engine) as session:
        championship = Championship(year=year)

        drivers = [Driver(first_name=driver.first_name, last_name=driver.last_name, nationality=driver.nationality, championship=championship) for driver in drivers_data]

        session.add_all(drivers)
        session.commit()
        session.refresh(championship, attribute_names=["drivers"])

    return championship 