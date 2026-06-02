from datetime import date

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import f1_race_analytics.app as app
from f1_race_analytics.database import (
    create_championship,
    create_race_results,
    create_races,
)
from f1_race_analytics.f1_data import ConstructorData, DriverData, Event, ResultData


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture
def race_events():
    return [
        Event(
            name="Australian Grand Prix",
            circuit_id="albert_park",
            date=date(2026, 3, 8),
            fp1_date=date(2026, 3, 6),
            circuit_name="Albert Park Grand Prix Circuit",
            circuit_locality="Melbourne",
            circuit_country="Australia",
            has_sprint=False,
        ),
        Event(
            name="Chinese Grand Prix",
            circuit_id="shanghai",
            date=date(2026, 3, 15),
            fp1_date=date(2026, 3, 13),
            circuit_name="Shanghai International Circuit",
            circuit_locality="Shanghai",
            circuit_country="China",
            has_sprint=True,
        ),
        Event(
            name="Japanese Grand Prix",
            circuit_id="suzuka",
            date=date(2026, 3, 29),
            fp1_date=date(2026, 3, 27),
            circuit_name="Suzuka Circuit",
            circuit_locality="Suzuka",
            circuit_country="Japan",
            has_sprint=False,
        ),
    ]


@pytest.fixture
def standings_pairs():
    return [
        (
            ConstructorData(
                constructor_id="ferrari", name="Ferrari", nationality="Italian"
            ),
            DriverData(
                driver_id="leclerc",
                number="16",
                first_name="Charles",
                last_name="Leclerc",
                nationality="Monegasque",
            ),
        ),
        (
            ConstructorData(
                constructor_id="ferrari", name="Ferrari", nationality="Italian"
            ),
            DriverData(
                driver_id="hamilton",
                number="44",
                first_name="Lewis",
                last_name="Hamilton",
                nationality="British",
            ),
        ),
        (
            ConstructorData(
                constructor_id="mercedes", name="Mercedes", nationality="German"
            ),
            DriverData(
                driver_id="antonelli",
                number="12",
                first_name="Andrea Kimi",
                last_name="Antonelli",
                nationality="Italian",
            ),
        ),
        (
            ConstructorData(
                constructor_id="mercedes", name="Mercedes", nationality="German"
            ),
            DriverData(
                driver_id="russell",
                number="63",
                first_name="George",
                last_name="Russell",
                nationality="British",
            ),
        ),
    ]


@pytest.fixture
def seeded_season(session, race_events, standings_pairs, monkeypatch):
    # Deliberately NOT the current calendar year: this makes the app.YEAR pin
    # below load-bearing. It locks down app.YEAR to a fixed value, instead of
    # letting it be whatever "datetime.now().year" returns.
    # Remove the monkeypatch and the year falls back to the value returned by
    # "datetime.now().year", but without 2099 data. So standings route tests
    # would go red now, instead of silently passing until the clock catches up.
    year = 2099
    monkeypatch.setattr(app, "YEAR", year)
    create_races(session, year, race_events)
    create_championship(session, year, standings_pairs)
    create_race_results(
        session,
        year,
        [
            ResultData("albert_park", "russell", "1", "25"),
            ResultData("albert_park", "antonelli", "2", "18"),
            ResultData("albert_park", "leclerc", "3", "15"),
            ResultData("albert_park", "hamilton", "4", "12"),
        ],
    )
    create_race_results(
        session,
        year,
        [
            ResultData("suzuka", "antonelli", "1", "25"),
            ResultData("suzuka", "leclerc", "3", "15"),
            ResultData("suzuka", "russell", "4", "12"),
            ResultData("suzuka", "hamilton", "6", "8"),
        ],
    )
    return session
