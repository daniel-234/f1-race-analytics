from typing import NamedTuple
from datetime import datetime, date

from .f1_data import fetch_races


# F1 Champioship season year
YEAR = 2026

class Event(NamedTuple):
    name: str
    date: date


def fetch_data() -> list[Event] | list[None]:
    races_data = fetch_races(YEAR)
    if races_data is None:
        print("Sorry, something went wrong")
        return []
    races = races_data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
    race_info = [Event(race.get('raceName', ""), _convert_to_dt(race.get('date', ''))) for race in races]
    
    print("\n\nRACES from Jolpica:\n")
    print(race_info)
    return race_info


def _convert_to_dt(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()


def main():
    fetch_data()


if __name__ == '__main__':
    main()