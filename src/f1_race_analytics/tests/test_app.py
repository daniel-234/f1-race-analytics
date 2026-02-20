import pytest

from f1_race_analytics.database import create_db_and_tables
from f1_race_analytics.app import create_races, create_constructors, create_drivers
from f1_race_analytics.f1_data import Event, ConstructorData, DriverData
from f1_race_analytics.models import Race, Constructor, Driver


@pytest.fixture(autouse=True)
def setup_database():
    create_db_and_tables()


@pytest.fixture
def race_events():
    return [
        Event(name="Australian Grand Prix", date="2026-03-15"),
        Event(name="Bahrain Grand Prix", date="2026-03-22"),
        Event(name="Chinese Grand Prix", date="2026-03-29"),
    ]


@pytest.fixture
def constructors_data():
    return [
        ConstructorData(name='Alpine F1 Team', nationality='French'), 
        ConstructorData(name='Aston Martin', nationality='British'), 
        ConstructorData(name='Audi', nationality='German')
    ]


@pytest.fixture
def drivers_data():
    return [
        DriverData(first_name='Alexander', last_name='Albon', nationality='Thai'), 
        DriverData(first_name='Fernando', last_name='Alonso', nationality='Spanish'), 
        DriverData(first_name='Andrea Kimi', last_name='Antonelli', nationality='Italian')
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


def test_create_constructors(constructors_data):
    championship = create_constructors(2026, constructors_data)
    assert championship.id == 2
    assert championship.year == 2026
    assert championship.constructors == [
        Constructor(id=1, nationality='French', championship_id=2, name='Alpine F1 Team'), 
        Constructor(id=2, nationality='British', championship_id=2, name='Aston Martin'), 
        Constructor(id=3, nationality='German', championship_id=2, name='Audi')
    ]


def test_create_drivers(drivers_data):
    championship = create_drivers(2026, drivers_data)
    assert championship.id == 3
    # Not asserting the year, as in 'create_drivers' session only the 'drivers' attribute was persisted
    assert championship.drivers == [
        Driver(first_name='Alexander', last_name='Albon', championship_id=3, nationality='Thai', id=1), 
        Driver(first_name='Fernando', last_name='Alonso', championship_id=3, nationality='Spanish', id=2), 
        Driver(first_name='Andrea Kimi', last_name='Antonelli', championship_id=3, nationality='Italian', id=3)
    ]
