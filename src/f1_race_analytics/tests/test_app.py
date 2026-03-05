from datetime import date

import pytest
from sqlmodel import Session, select

from f1_race_analytics.database import (
    clear_db_and_tables,
    create_championship,
    create_db_and_tables,
    create_races,
    engine,
)
from f1_race_analytics.f1_data import ConstructorData, DriverData, Event
from f1_race_analytics.models import (
    Championship,
    ChampionshipEntryLink,
    Constructor,
    Driver,
    Race,
)


@pytest.fixture(autouse=True)
def setup_database():
    clear_db_and_tables()
    create_db_and_tables()


@pytest.fixture
def race_events():
    return [
        Event(
            name="Australian Grand Prix",
            circuit_id="albert_park",
            date=date(2026, 3, 8),
            circuit_name="Albert Park Grand Prix Circuit",
            circuit_locality="Melbourne",
            circuit_country="Australia",
        ),
        Event(
            name="Chinese Grand Prix",
            circuit_id="shanghai",
            date=date(2026, 3, 15),
            circuit_name="Shanghai International Circuit",
            circuit_locality="Shanghai",
            circuit_country="China",
        ),
        Event(
            name="Japanese Grand Prix",
            circuit_id="suzuka",
            date=date(2026, 3, 29),
            circuit_name="Suzuka Circuit",
            circuit_locality="Suzuka",
            circuit_country="Japan",
        ),
    ]


@pytest.fixture
def constructor_driver_pairs():
    return [
        (
            ConstructorData(
                constructor_id="alpine", name="Alpine F1 Team", nationality="French"
            ),
            DriverData(
                driver_id="colapinto",
                number="43",
                first_name="Franco",
                last_name="Colapinto",
                nationality="Argentine",
            ),
        ),
        (
            ConstructorData(
                constructor_id="alpine", name="Alpine F1 Team", nationality="French"
            ),
            DriverData(
                driver_id="gasly",
                number="10",
                first_name="Pierre",
                last_name="Gasly",
                nationality="French",
            ),
        ),
        (
            ConstructorData(
                constructor_id="aston_martin",
                name="Aston Martin",
                nationality="British",
            ),
            DriverData(
                driver_id="alonso",
                number="14",
                first_name="Fernando",
                last_name="Alonso",
                nationality="Spanish",
            ),
        ),
        (
            ConstructorData(
                constructor_id="aston_martin",
                name="Aston Martin",
                nationality="British",
            ),
            DriverData(
                driver_id="stroll",
                number="18",
                first_name="Lance",
                last_name="Stroll",
                nationality="Canadian",
            ),
        ),
    ]


def test_create_races(race_events):
    championship = create_races(2026, race_events)
    assert championship.id == 1
    assert championship.year == 2026
    assert championship.races == [
        Race(
            date=date(2026, 3, 8),
            id=1,
            circuit_locality="Melbourne",
            championship_id=1,
            name="Australian Grand Prix",
            circuit_id="albert_park",
            circuit_name="Albert Park Grand Prix Circuit",
            circuit_country="Australia",
        ),
        Race(
            date=date(2026, 3, 15),
            id=2,
            circuit_locality="Shanghai",
            championship_id=1,
            name="Chinese Grand Prix",
            circuit_id="shanghai",
            circuit_name="Shanghai International Circuit",
            circuit_country="China",
        ),
        Race(
            date=date(2026, 3, 29),
            id=3,
            circuit_locality="Suzuka",
            championship_id=1,
            name="Japanese Grand Prix",
            circuit_id="suzuka",
            circuit_name="Suzuka Circuit",
            circuit_country="Japan",
        ),
    ]


def test_create_championship(constructor_driver_pairs):
    create_championship(2026, constructor_driver_pairs)
    with Session(engine) as read_session:
        all_championships = read_session.exec(select(Championship)).all()
        all_links = read_session.exec(select(ChampionshipEntryLink)).all()
        print("Championships:", all_championships)
        print("Links:", all_links)

    with Session(engine) as read_session:
        championship = read_session.exec(
            select(Championship).where(Championship.year == 2026)
        ).first()

        assert championship is not None

        links = read_session.exec(
            select(ChampionshipEntryLink).where(
                ChampionshipEntryLink.championship_id == championship.id
            )
        ).all()
        pairs = [(link.constructor, link.driver) for link in links]

        assert championship.year == 2026
        assert pairs == [
            (
                Constructor(
                    nationality="French",
                    constructor_id="alpine",
                    name="Alpine F1 Team",
                    id=1,
                ),
                Driver(
                    driver_id="colapinto",
                    last_name="Colapinto",
                    id=1,
                    number="43",
                    first_name="Franco",
                    nationality="Argentine",
                ),
            ),
            (
                Constructor(
                    nationality="French",
                    constructor_id="alpine",
                    name="Alpine F1 Team",
                    id=1,
                ),
                Driver(
                    driver_id="gasly",
                    last_name="Gasly",
                    id=2,
                    number="10",
                    first_name="Pierre",
                    nationality="French",
                ),
            ),
            (
                Constructor(
                    nationality="British",
                    constructor_id="aston_martin",
                    name="Aston Martin",
                    id=2,
                ),
                Driver(
                    driver_id="alonso",
                    last_name="Alonso",
                    id=3,
                    number="14",
                    first_name="Fernando",
                    nationality="Spanish",
                ),
            ),
            (
                Constructor(
                    nationality="British",
                    constructor_id="aston_martin",
                    name="Aston Martin",
                    id=2,
                ),
                Driver(
                    driver_id="stroll",
                    last_name="Stroll",
                    id=4,
                    number="18",
                    first_name="Lance",
                    nationality="Canadian",
                ),
            ),
        ]


def test_contructor_drivers_association(constructor_driver_pairs):
    create_championship(2026, constructor_driver_pairs)
    with Session(engine) as read_session:
        championship = read_session.exec(
            select(Championship).where(Championship.year == 2026)
        ).first()

        assert championship is not None

        links = read_session.exec(
            select(ChampionshipEntryLink).where(
                ChampionshipEntryLink.championship_id == championship.id
            )
        ).all()
        pairs = [(link.constructor, link.driver) for link in links]
        assert pairs[2] == (
            Constructor(
                nationality="British",
                constructor_id="aston_martin",
                name="Aston Martin",
                id=2,
            ),  # not 3
            Driver(
                driver_id="alonso",
                last_name="Alonso",
                id=3,
                number="14",
                first_name="Fernando",
                nationality="Spanish",
            ),
        )


def test_championship_entry_link():
    """
    Test the 3-way link table (ChampionshipEntryLink) that connects
    Championship, Constructor, and Driver.
    This pattern allows us to model: "Driver X drove for Constructor Y
    in Championship Z" - a many-to-many-to-many relationship.
    """
    from sqlmodel import Session

    from f1_race_analytics.database import engine
    from f1_race_analytics.models import Championship

    with Session(engine) as session:
        # Step 1: Create the parent entities independently
        championship = Championship(year=2025)
        session.add(championship)
        session.commit()
        session.refresh(championship)

        ferrari = Constructor(
            constructor_id="ferrari", name="Ferrari", nationality="Italian"
        )
        mercedes = Constructor(
            constructor_id="mercedes", name="Mercedes", nationality="German"
        )
        session.add_all([ferrari, mercedes])
        session.commit()
        session.refresh(ferrari)
        session.refresh(mercedes)

        leclerc = Driver(
            driver_id="leclerc",
            number="16",
            first_name="Charles",
            last_name="Leclerc",
            nationality="Monegasque",
        )
        hamilton = Driver(
            driver_id="hamilton",
            number="44",
            first_name="Lewis",
            last_name="Hamilton",
            nationality="British",
        )
        session.add_all([leclerc, hamilton])
        session.commit()
        session.refresh(leclerc)
        session.refresh(hamilton)

        # Step 2: Create the link entries using the IDs from the parent entities
        # Each link represents: "This driver drove for this constructor in this championship"

        # Ensure all entities were persisted before creating links
        assert championship.id is not None
        assert ferrari.id is not None
        assert leclerc.id is not None

        link1 = ChampionshipEntryLink(
            championship_id=championship.id,
            constructor_id=ferrari.id,
            driver_id=leclerc.id,
        )

        assert championship.id is not None
        assert mercedes.id is not None
        assert hamilton.id is not None

        link2 = ChampionshipEntryLink(
            championship_id=championship.id,
            constructor_id=mercedes.id,
            driver_id=hamilton.id,
        )
        session.add_all([link1, link2])
        session.commit()

        # Step 3: Verify navigation from Championship -> entries
        session.refresh(championship)
        assert len(championship.entry_links) == 2

        # Step 4: Verify navigation from Constructor -> entries -> Driver
        session.refresh(ferrari)
        assert len(ferrari.entry_links) == 1
        assert ferrari.entry_links[0].driver.last_name == "Leclerc"

        # Step 5: Verify navigation from Driver -> entries -> Constructor and Championship
        session.refresh(hamilton)
        assert len(hamilton.entry_links) == 1
        assert hamilton.entry_links[0].constructor.name == "Mercedes"
        assert hamilton.entry_links[0].championship.year == 2025
