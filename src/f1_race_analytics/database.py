from collections.abc import Sequence

from sqlmodel import Session, SQLModel, create_engine, select

from .f1_data import ConstructorData, DriverData, Event, ResultData
from .models import (
    Championship,
    ChampionshipEntryLink,
    Constructor,
    Driver,
    Race,
    RaceResult,
)

sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def clear_db_and_tables():
    SQLModel.metadata.drop_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def get_all_races(session: Session) -> Sequence[Race]:
    """
    Retrieve all races from the database
    """
    statement = select(Race)
    races = session.exec(statement).all()
    return races


def get_race_by_circuit_id(session: Session, circuit_id: str) -> Race | None:
    statement = select(Race).where(Race.circuit_id == circuit_id)
    race = session.exec(statement).first()
    return race


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


# TODO: Check UI for a button to call this function
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
                driver_id=driver_data.driver_id,
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


def create_results(year: int, race_result_data: list[ResultData]) -> RaceResult:
    """
    Create the RaceResult table, linking results to races for a given year
    """
    with Session(engine) as session:
        championship = Championship(year=year)
        session.add(championship)
        session.commit()
        session.refresh(championship)

        results = [
            RaceResult(
                race_id=race_result.circuit_id,
                driver_id=race_result.driver_id,
                position=race_result.position,
                points=race_result.points,
            )
            for race_result in race_result_data
        ]

        session.add_all(results)
        session.commit()

        # refresh each RaceResult object
        for result in results:
            session.refresh(result)

    return results
