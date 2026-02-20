import httpx
from typing import NamedTuple
from datetime import datetime, date


JOLPICA_ENDPOINT = "https://api.jolpi.ca/ergast/f1"
RACES = "races"


class Event(NamedTuple):
    name: str
    date: date


class ConstructorData(NamedTuple):
    name: str
    nationality: str


def fetch_races(year) -> list[Event] | list[None]:
    """
    Get the races for the given year
    """
    races_data = _fetch_data(year, "races")
    if races_data is None:
        print("Sorry, something went wrong")
        return []
    races = races_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    race_info = [Event(race.get('raceName', ""), _convert_to_dt(race.get('date', ''))) for race in races]
    return race_info


def fetch_constructors(year) -> list[ConstructorData] | list[None]:
    """
    Get the constructors for the given year
    """
    constructors_data = _fetch_data(year, "constructors")
    if constructors_data is None:
        print("Sorry, something went wrong")
        return []
    constructors = constructors_data.get("MRData", {}).get("ConstructorTable", {}).get("Constructors", [])
    constructor_info = [ConstructorData(constructor.get('name', ""), constructor.get("nationality", "")) for constructor in constructors]
    return constructor_info


def _convert_to_dt(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()


def _fetch_data(year: int, endpoint: str) -> dict[str, dict] | None:
    """
    Retrieve historical data from Jolpica F1 API:
    """
    try:
        response = httpx.get(f"{JOLPICA_ENDPOINT}/{year}/{endpoint}/")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Failed to fetch races for {year}: {e.response.status_code}")
        return None
    except httpx.RequestError as e:
        print(f"Network error: {e}")
        return None 