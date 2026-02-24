import pytest
from sqlmodel import Session, select, SQLModel

from f1_race_analytics.database import create_db_and_tables, clear_db_and_tables, engine 
from f1_race_analytics.app import create_races, create_championship  
from f1_race_analytics.f1_data import Event, ConstructorData, DriverData
from f1_race_analytics.models import Race, Constructor, Driver, Championship, ChampionshipEntryLink


@pytest.fixture(autouse=True)
def setup_database():
    clear_db_and_tables()
    create_db_and_tables()


@pytest.fixture
def race_events():
    return [
        Event(name="Australian Grand Prix", date="2026-03-15"),
        Event(name="Bahrain Grand Prix", date="2026-03-22"),
        Event(name="Chinese Grand Prix", date="2026-03-29"),
    ]


@pytest.fixture
def constructor_driver_pairs():
    return [
        (ConstructorData(constructor_id='alpine', name='Alpine F1 Team', nationality='French'), DriverData(number='43', first_name='Franco', last_name='Colapinto', nationality='Argentine')),
        (ConstructorData(constructor_id='alpine', name='Alpine F1 Team', nationality='French'), DriverData(number='10', first_name='Pierre', last_name='Gasly', nationality='French')),
        (ConstructorData(constructor_id='aston_martin', name='Aston Martin', nationality='British'), DriverData(number='14', first_name='Fernando', last_name='Alonso', nationality='Spanish')),
        (ConstructorData(constructor_id='aston_martin', name='Aston Martin', nationality='British'), DriverData(number='18', first_name='Lance', last_name='Stroll', nationality='Canadian'))
    ]


def test_create_races(race_events):
    championship = create_races(2026, race_events)
    assert championship.id == 1
    assert championship.year == 2026
    assert championship.races == [
        Race(id=1, name="Australian Grand Prix", championship_id=1),
        Race(id=2, name="Bahrain Grand Prix", championship_id=1),
        Race(id=3, name="Chinese Grand Prix", championship_id=1),
    ]


def test_create_championship(constructor_driver_pairs):
    create_championship(2026, constructor_driver_pairs)


    with Session(engine) as read_session:
        all_championships = read_session.exec(select(Championship)).all()
        all_links = read_session.exec(select(ChampionshipEntryLink)).all()
        print("Championships:", all_championships)
        print("Links:", all_links)


    with Session(engine) as read_session:
        championship = read_session.exec(select(Championship).where(Championship.year==2026)).first()
        links = read_session.exec(select(ChampionshipEntryLink).where(ChampionshipEntryLink.championship_id == championship.id)).all()
        pairs = [(link.constructor, link.driver) for link in links]
        assert championship.year == 2026
        assert pairs == [
            (Constructor(nationality='French', constructor_id='alpine', name='Alpine F1 Team', id=1), Driver(last_name='Colapinto', id=1, number='43', first_name='Franco', nationality='Argentine')),
            (Constructor(nationality='French', constructor_id='alpine', name='Alpine F1 Team', id=1), Driver(last_name='Gasly', id=2, number='10', first_name='Pierre', nationality='French')),
            (Constructor(nationality='British', constructor_id='aston_martin', name='Aston Martin', id=2), Driver(last_name='Alonso', id=3, number='14', first_name='Fernando', nationality='Spanish')),
            (Constructor(nationality='British', constructor_id='aston_martin', name='Aston Martin', id=2), Driver(last_name='Stroll', id=4, number='18', first_name='Lance', nationality='Canadian')),
        ]


def test_contructor_drivers_association(constructor_driver_pairs):
    create_championship(2026, constructor_driver_pairs)
    
    with Session(engine) as read_session:
        championship = read_session.exec(select(Championship).where(Championship.year == 2026)).first()
        links = read_session.exec(select(ChampionshipEntryLink).where(ChampionshipEntryLink.championship_id == championship.id)).all()
        pairs = [(link.constructor, link.driver) for link in links]
        assert pairs[2] == (Constructor(nationality='British', constructor_id='aston_martin', name='Aston Martin', id=2), Driver(last_name='Alonso', id=3, number='14', first_name='Fernando', nationality='Spanish'))