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


def get_result_by_circuit_id(
    session: Session, circuit_id: str
) -> list[RaceResult] | None:
    statement = select(Race).where(Race.circuit_id == circuit_id)
    race = session.exec(statement).first()
    saved_result = select(RaceResult).where(RaceResult.race_id == race.id)
    race_result = session.exec(saved_result).all()
    return race_result


def select_championship_by_year(year: int, session: Session) -> Championship:
    # Check if there is already a Championship instance for "year";
    # otherwise, create one
    statement = select(Championship).where(Championship.year == year)
    championship = session.exec(statement).first()
    if championship is None:
        championship = Championship(year=year)
    return championship


def create_races(year: int, races_data: list[Event]) -> Championship:
    """
    Create the championship and races instances for the given year
    """
    with Session(engine) as session:
        championship = select_championship_by_year(year, session)

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
        championship = select_championship_by_year(year, session)

        for constructor_data, driver_data in constructor_driver_pairs:
            constructor = Constructor(
                constructor_id=constructor_data.constructor_id,
                name=constructor_data.name,
                nationality=constructor_data.nationality,
            )
            driver = Driver(
                driver_id=driver_data.driver_id,
                number=driver_data.number,
                first_name=driver_data.first_name,
                last_name=driver_data.last_name,
                nationality=driver_data.nationality,
            )
            session.add(constructor)
            session.add(driver)
            session.commit()
            session.refresh(constructor)
            session.refresh(driver)

            link = ChampionshipEntryLink(
                championship_id=championship.id,
                constructor_id=constructor.id,
                driver_id=driver.id,
            )

            session.add(link)
            session.commit()
            session.refresh(link)

        session.refresh(championship)

    return championship


def create_race_results(
    year: int, race_result_data: list[ResultData]
) -> list[RaceResult]:
    """
    Create the RaceResult table, linking results to races for a given year
    """
    with Session(engine) as session:
        championship = select_championship_by_year(year, session)

        race_statement = select(Race).where(
            Race.circuit_id == race_result_data[0].circuit_id
        )
        race = session.exec(race_statement).first()
        # TODO See if it is still needed
        drivers_statement = select(Driver)
        session.exec(drivers_statement).all()

        for race_result in race_result_data:
            driver = session.exec(
                select(Driver).where(Driver.driver_id == race_result.driver_id)
            ).first()
            if driver is None:
                continue
            result = RaceResult(
                race_id=race.id,
                driver_id=driver.id,
                position=race_result.position,
                points=race_result.points,
            )
            session.add(result)
            session.commit()
            session.refresh(result)

        session.refresh(championship)

    return championship
