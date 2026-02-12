import httpx


jolpica_endpoint = "https://api.jolpi.ca/ergast/f1"
races = "races"

async def fetch_races(year: int) -> list[dict]:
    """
    Retrieve historical data from Jolpica F1 API:
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{jolpica_endpoint}/{str(year)}/{races}/")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Failed to fetch races for {year}: {e.response.status_code}")
        return []
    except httpx.RequestError as e:
        print(f"Network error: {e}")
        return []