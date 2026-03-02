"""
NiceGUI prototype for F1 Race Analytics.

Run the API first:
    uv run fastapi dev src/f1_race_analytics/app.py

Then run this UI:
    uv run python -m f1_race_analytics.ui
"""

from datetime import date

import httpx
from nicegui import ui

API_BASE_URL = "http://localhost:8000"


def is_race_live(race_date_str: str) -> bool:
    race_date = date.fromisoformat(race_date_str) if race_date_str else None
    if race_date is None:
        return False
    today = date.today()
    return race_date == today


def fetch_races() -> list[dict]:
    try:
        response = httpx.get(f"{API_BASE_URL}/races", timeout=5.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return []


def fetch_race(circuit_id: str) -> dict | None:
    try:
        response = httpx.get(f"{API_BASE_URL}/races/{circuit_id}", timeout=5.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return None


@ui.page("/")
def index():
    races = fetch_races()

    with ui.header().classes("bg-red-600 text-white"):
        ui.label("F1 Race Analytics 2026").classes("text-2xl font-bold")

    with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
        ui.label("2026 Race Calendar").classes("text-xl font-semibold mb-4")

        if not races:
            ui.label("No races found. Is the API running?").classes("text-red-500")
            ui.label(
                "Start the API with: uv run fastapi dev src/f1_race_analytics/app.py"
            )
            return

        for race in races:
            live = is_race_live(race.get("date", ""))
            with ui.card().classes("w-full mb-2 hover:shadow-lg cursor-pointer"):
                with ui.row().classes("items-center justify-between w-full"):
                    with ui.column():
                        ui.label(race["name"]).classes("font-semibold")
                        ui.label(
                            f"{race['circuit_name']} - {race['circuit_locality']}, {race['circuit_country']}"
                        ).classes("text-sm text-gray-600")
                        ui.label(race.get("date", "")).classes("text-xs text-gray-400")
                    with ui.row().classes("items-center gap-2"):
                        if live:
                            ui.badge("LIVE", color="red").classes("animate-pulse")
                        ui.link(
                            "View Details",
                            f"/race/{race['circuit_id']}",
                        ).classes("text-blue-500")


@ui.page("/race/{circuit_id}")
def race_detail(circuit_id: str):
    race = fetch_race(circuit_id)

    with ui.header().classes("bg-red-600 text-white"):
        ui.label("F1 Race Analytics 2026").classes("text-2xl font-bold")

    with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
        ui.link("< Back to Calendar", "/").classes("text-blue-500 mb-4")

        if race is None:
            ui.label(f"Race not found: {circuit_id}").classes("text-red-500")
            return

        live = is_race_live(race.get("date", ""))

        with ui.card().classes("w-full"):
            with ui.row().classes("items-center gap-4"):
                ui.label(race["name"]).classes("text-2xl font-bold")
                if live:
                    ui.badge("LIVE", color="red").classes("animate-pulse text-lg")

            ui.separator()

            with ui.column().classes("gap-2"):
                ui.label(f"{race['circuit_name']}").classes("text-lg")
                ui.label(
                    f"{race['circuit_locality']}, {race['circuit_country']}"
                ).classes("text-gray-600")
                ui.label(f"Date: {race.get('date', 'TBD')}").classes("text-gray-500")

        ui.label("Live timing data will appear here during race weekend").classes(
            "mt-4 text-gray-500 italic"
        )


def main():
    ui.run(title="F1 Race Analytics", port=8080)


if __name__ in {"__main__", "__mp_main__"}:
    main()
