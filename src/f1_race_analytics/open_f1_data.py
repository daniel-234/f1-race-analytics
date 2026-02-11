"""
The OpenF1 API refers to meetings for both Grand Prix and testing sessions

TODO: get a list of GPs only

"""

import httpx 


async def fetch_meetings() -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.openf1.org/v1/meetings?year=2026")
        response.raise_for_status()
        return response.json()