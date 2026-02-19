import httpx


JOLPICA_ENDPOINT = "https://api.jolpi.ca/ergast/f1"
RACES = "races"

def fetch_races(year: int) -> dict[str, dict] | None:
    """
    Retrieve historical data from Jolpica F1 API:
    """
    try:
        response = httpx.get(f"{JOLPICA_ENDPOINT}/{str(year)}/{RACES}/")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Failed to fetch races for {year}: {e.response.status_code}")
        return None
    except httpx.RequestError as e:
        print(f"Network error: {e}")
        return None 