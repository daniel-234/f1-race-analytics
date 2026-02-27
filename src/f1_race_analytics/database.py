from sqlmodel import Session, SQLModel, create_engine

from .f1_data import ConstructorData, DriverData, Event
from .models import Championship, ChampionshipEntryLink, Constructor, Driver, Race

sqlite_url = "sqlite:///:memory:"
engine = create_engine(sqlite_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def clear_db_and_tables():
    SQLModel.metadata.drop_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def create_races(year: int, races_data: list[Event]) -> Championship:
    """
    Create the chanpionship and races instances for the given year
    """
    with Session(engine) as session:
        championship = Championship(year=year)

        races = [
            Race(
                name=race.name,
                circuit_id=race.circuit_id,
                date=race.date,
                circuit_name=race.circuit_name,
                circuit_locality=race.circuit_locality,
                circuit_country=race.circuit_country,
                championship=championship,
            )
            for race in races_data
        ]

        session.add_all(races)
        session.commit()
        session.refresh(championship, attribute_names=["year", "races"])
    return championship


def create_championship(
    year: int, constructor_driver_pairs: list[tuple[ConstructorData, DriverData]]
) -> Championship:
    """
    Create the championship and the linked tables for constructors and their drivers
    """
    with Session(engine) as session:
        championship = Championship(year=year)
        session.add(championship)
        session.commit()
        session.refresh(championship)

        constructors = {}  # cache by constructor_id to avoid duplicates

        for constructor_data, driver_data in constructor_driver_pairs:
            # reuse constructor if already created
            if constructor_data.constructor_id not in constructors:
                constructor = Constructor(
                    constructor_id=constructor_data.constructor_id,
                    name=constructor_data.name,
                    nationality=constructor_data.nationality,
                )
                session.add(constructor)
                session.flush()
                constructors[constructor_data.constructor_id] = constructor

            driver = Driver(
                number=driver_data.number,
                first_name=driver_data.first_name,
                last_name=driver_data.last_name,
                nationality=driver_data.nationality,
            )
            session.add(driver)
            session.commit()
            session.refresh(driver)

            link = ChampionshipEntryLink(
                championship_id=championship.id,
                constructor_id=constructors[constructor_data.constructor_id].id,
                driver_id=driver.id,
            )
            session.add(link)

        session.commit()

    return championship
