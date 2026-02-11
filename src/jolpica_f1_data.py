"""
Data to be retrieved for 2026:
    - race names
    - circuits
    - locations
    - dates 
"""

import httpx
import asyncio


async def fetch_races() -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.jolpi.ca/ergast/f1/2026/races/")
        response.raise_for_status()
        return response.json()


async def main():
    races = await fetch_races()
    print(races)


asyncio.run(main())