import asyncio
import json
import ssl
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

import httpx
import paho.mqtt.client as mqtt
import uvicorn
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.fastapi import DatastarResponse
from decouple import config
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="F1 Live Dashboard")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

OPENF1_API = "https://api.openf1.org/v1"
OPENF1_TOKEN_URL = "https://api.openf1.org/token"
OPENF1_MQTT_BROKER = "mqtt.openf1.org"
OPENF1_MQTT_PORT = 8883

_cached_token: str | None = None


@dataclass
class DriverStanding:
    position: int
    change: int


async def get_access_token() -> str:
    global _cached_token
    if _cached_token:
        return _cached_token

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            OPENF1_TOKEN_URL,
            data={
                "username": config("OPENF1_USERNAME"),
                "password": config("OPENF1_PASSWORD"),
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        _cached_token = resp.json()["access_token"]
        return _cached_token


def render_positions(
    standings: dict[int, DriverStanding], drivers: dict[int, str]
) -> str:
    """
    Render the drivers positions table body as HTML
    """
    rows = []
    table_rows = []
    for driver_number, standing in standings.items():
        rows.append((driver_number, standing.position, standing.change))
    for row in sorted(rows, key=lambda x: x[1])[:10]:
        number, position, change = row
        arrow = "▲" if change < 0 else "▼" if change > 0 else ""
        tr = f"<tr><td>P{position}</td><td>{number}</td><td>{arrow} {abs(change)}</td></tr>"
        table_rows.append(tr)

    return f'<div id="positions" class="panel"><h2>Positions</h2><table><tr><th>Pos</th><th>Driver</th></tr>{"\n".join(table_rows)}</table></div>'


RACES = [
    {
        "round": "01",
        "location": "Australia",
        "circuit": "Albert Park, Melbourne",
        "date": "6 – 8 Mar",
        "sprint": False,
    },
    {
        "round": "02",
        "location": "China",
        "circuit": "Shanghai Int'l Circuit",
        "date": "13 – 15 Mar",
        "sprint": True,
    },
    {
        "round": "03",
        "location": "Japan",
        "circuit": "Suzuka Circuit",
        "date": "27 – 29 Mar",
        "sprint": False,
    },
    {
        "round": "04",
        "location": "Bahrain",
        "circuit": "Bahrain Int'l Circuit",
        "date": "10 – 12 Apr",
        "sprint": False,
    },
    {
        "round": "05",
        "location": "Saudi Arabia",
        "circuit": "Jeddah Corniche Circuit",
        "date": "17 – 19 Apr",
        "sprint": False,
    },
    {
        "round": "06",
        "location": "Miami",
        "circuit": "Miami Int'l Autodrome",
        "date": "1 – 3 May",
        "sprint": True,
    },
    {
        "round": "07",
        "location": "Canada",
        "circuit": "Circuit Gilles Villeneuve",
        "date": "22 – 24 May",
        "sprint": True,
    },
    {
        "round": "08",
        "location": "Monaco",
        "circuit": "Circuit de Monaco",
        "date": "5 – 7 Jun",
        "sprint": False,
    },
    {
        "round": "09",
        "location": "Barcelona",
        "circuit": "Circuit de Catalunya",
        "date": "12 – 14 Jun",
        "sprint": False,
    },
    {
        "round": "10",
        "location": "Austria",
        "circuit": "Red Bull Ring, Spielberg",
        "date": "26 – 28 Jun",
        "sprint": False,
    },
    {
        "round": "11",
        "location": "Great Britain",
        "circuit": "Silverstone Circuit",
        "date": "3 – 5 Jul",
        "sprint": True,
    },
    {
        "round": "12",
        "location": "Belgium",
        "circuit": "Circuit de Spa-Franc.",
        "date": "17 – 19 Jul",
        "sprint": False,
    },
    {
        "round": "13",
        "location": "Hungary",
        "circuit": "Hungaroring, Budapest",
        "date": "24 – 26 Jul",
        "sprint": False,
    },
    {
        "round": "14",
        "location": "Netherlands",
        "circuit": "Zandvoort Circuit",
        "date": "21 – 23 Aug",
        "sprint": True,
    },
    {
        "round": "15",
        "location": "Italy",
        "circuit": "Autodromo di Monza",
        "date": "4 – 6 Sep",
        "sprint": False,
    },
    {
        "round": "16",
        "location": "Madrid",
        "circuit": "Madrid Street Circuit",
        "date": "11 – 13 Sep",
        "sprint": False,
    },
    {
        "round": "17",
        "location": "Azerbaijan",
        "circuit": "Baku City Circuit",
        "date": "25 – 27 Sep",
        "sprint": False,
    },
    {
        "round": "18",
        "location": "Singapore",
        "circuit": "Marina Bay Street Circuit",
        "date": "9 – 11 Oct",
        "sprint": True,
    },
    {
        "round": "19",
        "location": "USA",
        "circuit": "Circuit of the Americas",
        "date": "23 – 25 Oct",
        "sprint": False,
    },
    {
        "round": "20",
        "location": "Mexico City",
        "circuit": "Autódromo Hermanos Rodríguez",
        "date": "30 Oct – 1 Nov",
        "sprint": False,
    },
    {
        "round": "21",
        "location": "São Paulo",
        "circuit": "Autódromo José Carlos Pace",
        "date": "6 – 8 Nov",
        "sprint": False,
    },
    {
        "round": "22",
        "location": "Las Vegas",
        "circuit": "Las Vegas Strip Circuit",
        "date": "20 – 22 Nov",
        "sprint": False,
    },
    {
        "round": "23",
        "location": "Qatar",
        "circuit": "Lusail Int'l Circuit",
        "date": "27 – 29 Nov",
        "sprint": False,
    },
    {
        "round": "24",
        "location": "Abu Dhabi",
        "circuit": "Yas Marina Circuit",
        "date": "4 – 6 Dec",
        "sprint": False,
    },
]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "2026 Season",
            "races": RACES,
        },
    )


@app.get("/live")
async def live_page(request: Request):
    """Serve the HTML page for replay."""
    return templates.TemplateResponse(
        "live_dashboard.html",
        {
            "request": request,
        },
    )


@app.get("/live/stream")
async def live_endpoint(request: Request, session_key: str):
    async def stream():
        # --- Auth ---
        try:
            token = await get_access_token()
        except Exception as e:
            yield SSE.patch_elements(
                f"""<div id="status" class="panel">Auth failed: {e}</div>"""
            )
            return

        # --- Fetch session metadata via authenticated REST ---
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{OPENF1_API}/sessions?session_key={session_key}",
                headers={"Authorization": f"Bearer {token}"},
            )
            sessions = resp.json() if resp.status_code == 200 else []

        if not sessions:
            yield SSE.patch_elements(
                """<div id="status" class="panel">Session not found.</div>"""
            )
            return

        session = sessions[0]

        yield SSE.patch_elements(f"""
            <div id="session-info" class="panel">
                <h2>{session.get('session_name', '')} — {session.get('circuit_short_name', '')}</h2>
            </div>
        """)

        # --- MQTT setup ---
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        topics = [
            "v1/location",
            "v1/laps",
            "v1/car_data",
            "v1/intervals",
            "v1/position",
        ]

        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                for topic in topics:
                    client.subscribe(topic)
            else:
                queue.put_nowait({"error": f"MQTT connect failed: rc={rc}"})

        def on_message(client, userdata, msg):
            try:
                data = json.loads(msg.payload.decode())
                if data.get("session_key") == session_key:
                    queue.put_nowait({"topic": msg.topic, "data": data})
            except Exception as e:
                queue.put_nowait({"error": str(e)})

        def on_disconnect(client, userdata, disconnect_flags, rc, properties=None):
            queue.put_nowait({"error": "MQTT disconnected"})

        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        mqtt_client.username_pw_set(username=config("OPENF1_USERNAME"), password=token)
        mqtt_client.tls_set(
            cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT
        )
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_disconnect = on_disconnect

        await loop.run_in_executor(
            None,
            lambda: mqtt_client.connect(OPENF1_MQTT_BROKER, OPENF1_MQTT_PORT, 60),
        )
        mqtt_client.loop_start()

        try:
            while True:
                try:
                    # Handle the situatio when there are no MQTT messages for 30 seconds
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)

                    if "error" in message:
                        yield SSE.patch_elements(f"""
                            <div id="status" class="panel">{message['error']}</div>
                        """)
                        break

                    topic = message["topic"]
                    data = message["data"]

                    if topic == "v1/laps":
                        driver = data.get("driver_number")
                        lap_number = data.get("lap_number")
                        # TODO Keep either patch_signals or patch_elements
                        yield SSE.patch_signals({"laps": {str(driver): lap_number}})
                        # yield SSE.patch_elements(f"""
                        #    <div id="f1-lap-{driver}">
                        #        Driver {driver} — Lap {data.get('lap_number')}
                        #    </div>
                        # """)

                    elif topic == "v1/position":
                        driver = data.get("driver_number")
                        position = data.get("position")
                        # TODO Keep either patch_signals or patch_elements
                        yield SSE.patch_signals({"positions": {str(driver): position}})
                        yield SSE.patch_elements(f"""
                            <div id="f1-position-{driver}">
                                Driver {driver} — P{position}
                            </div>
                        """)

                except asyncio.TimeoutError:
                    # Keep the SSE connection even when there are no MQTT messages for
                    # 30 seconds, so the browser keeps the connection active.
                    yield SSE.patch_elements("""<span id="f1-ping" hidden></span>""")

        finally:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

    return DatastarResponse(stream())


@app.get("/replay")
async def replay_page(request: Request):
    """Serve the HTML page for replay."""
    return templates.TemplateResponse(
        "replay_dashboard.html",
        {
            "request": request,
        },
    )


@app.get("/replay/stream")
async def replay_session(session_key: str = "9839", speed: float = 1):
    """Stream replay data via SSE."""

    async def stream():
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OPENF1_API}/sessions?session_key={session_key}")
            sessions = resp.json() if resp.status_code == 200 else []

            if sessions:
                s = sessions[0]
                yield SSE.patch_elements(
                    f'<div id="session-info" class="panel"><h2>{s.get("session_name")} - {s.get("location")}</h2></div>'
                )

            # Fetch driver names
            resp = await client.get(f"{OPENF1_API}/drivers?session_key={session_key}")
            driver_data = resp.json() if resp.status_code == 200 else []
            drivers = {
                d["driver_number"]: d.get("name_acronym", f"#{d['driver_number']}")
                for d in driver_data
            }

            resp = await client.get(f"{OPENF1_API}/position?session_key={session_key}")
            positions = resp.json() if resp.status_code == 200 else []

        if not positions:
            yield SSE.patch_elements(
                '<div id="status" class="panel"><p>No data found</p></div>'
            )
            return

        sorted_positions = sorted(positions, key=lambda x: x.get("date", ""))
        grouped = groupby(sorted_positions, key=lambda x: x.get("date", ""))

        standings: dict[int, DriverStanding] = {}
        count = 0

        for timestamp, group in grouped:
            count += 1
            if count > 50:
                break

            for p in group:
                driver, pos = p.get("driver_number"), p.get("position")
                if driver and pos:
                    # Store the drivers' previous standings to compare them with
                    # the new positions and check if there has been a change
                    previous_position = (
                        pos if count == 1 else standings[driver].position
                    )
                    new_position = pos
                    change = new_position - previous_position
                    standings[driver] = DriverStanding(
                        position=new_position, change=change
                    )

            # Send an SSE event that updates the positions table returned by "render_positions"
            # by using Datastar's patching/morphing mechanism.
            yield SSE.patch_elements(render_positions(standings, drivers))

            time_short = timestamp[11:19] if len(timestamp) > 19 else timestamp
            # Stream is in progress; patch the container DIV for status update.
            yield SSE.patch_elements(
                f'<div id="status" class="panel" style="background: #f0fff0;"><p>Update {count} - {time_short}</p></div>'
            )

            await asyncio.sleep(speed)

        # Stream has completed; patch the container DIV for status complete
        yield SSE.patch_elements(
            '<div id="status" class="panel" style="background: #f0fff0;"><p>Replay complete</p></div>'
        )

    return DatastarResponse(stream())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
