import asyncio

from jolpica_f1_data import fetch_races
from open_f1_data import fetch_meetings


async def main():
    races = await fetch_races()
    meetings = await fetch_meetings()
    print("RACES from Jolpica:\n")
    print(races)
    print("\n\nMeetings from OpenF1:")
    print(meetings)


asyncio.run(main())