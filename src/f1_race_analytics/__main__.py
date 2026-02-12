import asyncio
from typing import NamedTuple
from datetime import datetime, date

from .f1_data import fetch_races


# F1 Champioship season year
year = 2026

class Event(NamedTuple):
    name: str
    date: date


async def fetch_data():
    races_data = await fetch_races(year)
    if not races_data:
        print("Sorry, something went wrong")
        return None
    races = races_data.get('MRData').get('RaceTable').get('Races')
    race_info = [Event(race.get('raceName', ""), _convert_to_dt(race.get('date'))) for race in races]
    
    print("\n\nRACES from Jolpica:\n")
    print(race_info)


def _convert_to_dt(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()


def main():
    asyncio.run(fetch_data())


if __name__ == '__main__':
    main()