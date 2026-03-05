from datetime import date, datetime
from typing import NamedTuple

import httpx

JOLPICA_ENDPOINT = "https://api.jolpi.ca/ergast/f1"
# RACES = "races"


class Event(NamedTuple):
    name: str
    circuit_id: str
    date: date
    circuit_name: str
    circuit_locality: str
    circuit_country: str


class ConstructorData(NamedTuple):
    # Identifies the constructor in the API database
    constructor_id: str
    name: str
    nationality: str


class DriverData(NamedTuple):
    # Identifies the driver in the driver database
    driver_id: str
    number: str
    first_name: str
    last_name: str
    nationality: str


class ResultData(NamedTuple):
    circuit_id: str
    driver_id: str
    position: str
    points: str


def fetch_races(year: int) -> list[Event]:
    """
    Get the races for the given year
    """
    races_data = _fetch_data(year, "races")
    if races_data is None:
        print("Sorry, something went wrong")
        return []
    races = races_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    race_info = [
        Event(
            race.get("raceName", ""),
            race.get("Circuit", {}).get("circuitId", ""),
            _convert_to_dt(race.get("date", "")),
            race.get("Circuit", {}).get("circuitName", ""),
            race.get("Circuit", {}).get("Location", {}).get("locality", ""),
            race.get("Circuit", {}).get("Location", {}).get("country", ""),
        )
        for race in races
    ]
    return race_info


def fetch_constructors(year: int) -> list[ConstructorData]:
    """
    Get the constructors for the given year
    """
    constructors_data = _fetch_data(year, "constructors")
    if constructors_data is None:
        print("Sorry, something went wrong")
        return []
    constructors = (
        constructors_data.get("MRData", {})
        .get("ConstructorTable", {})
        .get("Constructors", [])
    )
    constructor_info = [
        ConstructorData(
            constructor.get("constructorId", ""),
            constructor.get("name", ""),
            constructor.get("nationality", ""),
        )
        for constructor in constructors
    ]
    return constructor_info


def fetch_constructor_driver_pairs(
    year: int,
) -> list[tuple[ConstructorData, DriverData]]:
    constructors = fetch_constructors(year)

    pairs = []
    for constructor in constructors:
        drivers = fetch_drivers_by_constructor(year, constructor.constructor_id)
        for driver in drivers:
            pairs.append((constructor, driver))
    return pairs


def fetch_drivers_by_constructor(year: int, constructor_id: str) -> list[DriverData]:
    drivers_data = _fetch_data(year, f"/constructors/{constructor_id}/drivers/")
    if drivers_data is None:
        print("Sorry, something went wrong")
        return []
    drivers = drivers_data.get("MRData", {}).get("DriverTable", {}).get("Drivers", [])
    driver_info = [
        DriverData(
            driver.get("driverId", ""),
            driver.get("permanentNumber", ""),
            driver.get("givenName", ""),
            driver.get("familyName", ""),
            driver.get("nationality", ""),
        )
        for driver in drivers
    ]
    return driver_info


def fetch_results_by_race(year: int, circuit_id: str) -> list[ResultData]:
    race_data = _fetch_data(year, f"circuits/{circuit_id}/results/")
    if race_data is None:
        print(f"No result for circuit {circuit_id}")
        return []
    # Get the single object returned by the API from the "Races" list
    results = (
        race_data.get("MRData", {})
        .get("RaceTable", {})
        .get("Races", [])[0]
        .get("Results", [])
    )
    result_info = [
        ResultData(
            circuit_id,
            result.get("Driver", {}).get("driverId", ""),
            result.get("position", ""),
            result.get("points", ""),
        )
        for result in results
    ]
    return result_info


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
        print(
            f"Failed to fetch data for {endpoint} for season {year}: {e.response.status_code}"
        )
        return None
    except httpx.RequestError as e:
        print(f"Network error: {e}")
        return None
