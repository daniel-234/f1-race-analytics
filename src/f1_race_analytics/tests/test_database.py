from datetime import date

import pytest
from sqlmodel import select

from f1_race_analytics.database import (
    create_championship,
    create_race_results,
    create_races,
    get_constructor_ranks,
    get_driver_ranks,
)
from f1_race_analytics.f1_data import (
    ConstructorData,
    DriverData,
    ResultData,
    SessionType,
)
from f1_race_analytics.models import (
    Championship,
    ChampionshipEntryLink,
    Constructor,
    Driver,
    Race,
)


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


@pytest.fixture
def seeded_standings(session, race_events, standings_pairs):
    """Seed two races of results; the rank tests' expected points are computed from this data."""
    australian_results = [
        ResultData("albert_park", "russell", "1", "25"),
        ResultData("albert_park", "antonelli", "2", "18"),
        ResultData("albert_park", "leclerc", "3", "15"),
        ResultData("albert_park", "hamilton", "4", "12"),
    ]
    japanese_results = [
        ResultData("suzuka", "antonelli", "1", "25"),
        ResultData("suzuka", "leclerc", "3", "15"),
        ResultData("suzuka", "russell", "4", "12"),
        ResultData(
            "suzuka",
            "hamilton",
            "6",
            "8",
        ),
    ]
    create_races(session, 2026, race_events)
    create_championship(session, 2026, standings_pairs)
    create_race_results(session, 2026, SessionType.GRAND_PRIX, australian_results)
    create_race_results(session, 2026, SessionType.GRAND_PRIX, japanese_results)


def test_create_races(session, race_events):
    championship = create_races(session, 2026, race_events)
    assert championship.id == 1
    assert championship.year == 2026
    assert championship.races == [
        Race(
            id=1,
            name="Australian Grand Prix",
            circuit_id="albert_park",
            date=date(2026, 3, 8),
            fp1_date=date(2026, 3, 6),
            circuit_name="Albert Park Grand Prix Circuit",
            circuit_locality="Melbourne",
            circuit_country="Australia",
            has_sprint=False,
            championship_id=1,
        ),
        Race(
            id=2,
            name="Chinese Grand Prix",
            circuit_id="shanghai",
            date=date(2026, 3, 15),
            fp1_date=date(2026, 3, 13),
            circuit_name="Shanghai International Circuit",
            circuit_locality="Shanghai",
            circuit_country="China",
            has_sprint=True,
            championship_id=1,
        ),
        Race(
            id=3,
            name="Japanese Grand Prix",
            circuit_id="suzuka",
            date=date(2026, 3, 29),
            fp1_date=date(2026, 3, 27),
            circuit_name="Suzuka Circuit",
            circuit_locality="Suzuka",
            circuit_country="Japan",
            has_sprint=False,
            championship_id=1,
        ),
    ]


def test_create_championship(session, constructor_driver_pairs):
    create_championship(session, 2026, constructor_driver_pairs)
    championship = session.exec(
        select(Championship).where(Championship.year == 2026)
    ).first()

    assert championship is not None

    links = session.exec(
        select(ChampionshipEntryLink).where(
            ChampionshipEntryLink.championship_id == championship.id
        )
    ).all()
    pairs = [(link.constructor, link.driver) for link in links]

    assert championship.year == 2026
    # constructors are deduped, so a team keeps one id (Aston is 2, not 3)
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


def test_create_championship_dedupes_shared_constructor(
    session, constructor_driver_pairs
):
    create_championship(session, 2026, constructor_driver_pairs)
    constructors = session.exec(select(Constructor)).all()
    assert len(constructors) == 2


def test_championship_entry_link(session):
    """
    Test the 3-way link table (ChampionshipEntryLink) that connects
    Championship, Constructor, and Driver.
    This pattern allows us to model: "Driver X drove for Constructor Y
    in Championship Z" - a many-to-many-to-many relationship.
    """

    # Built by hand instead of via create_championship: this test targets the ORM
    # relationships (the entry_links navigation below), so staying off the mutator
    # keeps it independent — a failure here points at the model wiring, not
    # create_championship.
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

    # Verify navigation from Championship -> entries
    session.refresh(championship)
    assert len(championship.entry_links) == 2

    # Verify navigation from Constructor -> entries -> Driver
    session.refresh(ferrari)
    assert len(ferrari.entry_links) == 1
    assert ferrari.entry_links[0].driver.last_name == "Leclerc"

    # Verify navigation from Driver -> entries -> Constructor and Championship
    session.refresh(hamilton)
    assert len(hamilton.entry_links) == 1
    assert hamilton.entry_links[0].constructor.name == "Mercedes"
    assert hamilton.entry_links[0].championship.year == 2025


def test_get_constructor_ranks(session, seeded_standings):
    standings = get_constructor_ranks(session, 2026)

    assert [(s.constructor.name, s.points) for s in standings] == [
        ("Mercedes", 80),
        ("Ferrari", 50),
    ]


def test_get_driver_ranks(session, seeded_standings):
    standings = get_driver_ranks(session, 2026)

    assert [(s.driver.last_name, s.points) for s in standings] == [
        ("Antonelli", 43),
        ("Russell", 37),
        ("Leclerc", 30),
        ("Hamilton", 20),
    ]


def test_sprint_points_count_toward_driver_standings(
    session, race_events, standings_pairs
):
    create_races(session, 2026, race_events)
    create_championship(session, 2026, standings_pairs)

    create_race_results(
        session,
        2026,
        SessionType.GRAND_PRIX,
        [
            ResultData(
                circuit_id="shanghai", driver_id="hamilton", position="3", points="15"
            ),
            ResultData(
                circuit_id="shanghai", driver_id="leclerc", position="4", points="12"
            ),
        ],
    )
    create_race_results(
        session,
        2026,
        SessionType.SPRINT,
        [
            ResultData(
                circuit_id="shanghai", driver_id="leclerc", position="2", points="7"
            ),
            ResultData(
                circuit_id="shanghai", driver_id="hamilton", position="3", points="6"
            ),
        ],
    )

    standings = get_driver_ranks(session, 2026)

    assert [(s.driver.last_name, s.points) for s in standings] == [
        ("Hamilton", 21),
        ("Leclerc", 19),
    ]
