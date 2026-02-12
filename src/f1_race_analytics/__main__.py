import asyncio

from .jolpica_f1_data import fetch_races
from .open_f1_data import fetch_meetings


async def fetch_data():
    races_data = await fetch_races()
    #meetings_data = await fetch_meetings()
    
    #grand_prix_names = [grand_prix_official for grand_prix_official in meetings_data.get("meeting_official_name")]
    #print("\n\nMeetings from OpenF1:")
    #print(grand_prix_names)

    races = races_data.get('MRData').get('RaceTable').get('Races')
    race_info = [(race.get('date'), race.get('raceName', {})) for race in races]
    
    print("\n\nRACES from Jolpica:\n")
    print(race_info)


def main():
    asyncio.run(fetch_data())


if __name__ == '__main__':
    main()