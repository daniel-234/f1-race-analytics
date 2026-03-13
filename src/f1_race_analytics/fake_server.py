"""
Fake OpenF1 server for testing live_api.py without a real F1 event.

Emulates:
- REST API endpoints (sessions, drivers, position, token)
- MQTT broker publishing simulated live data

Usage:
    uv run python -m f1_race_analytics.fake_server

Then configure live_api.py to point to localhost:1221 (REST) and localhost:1883 (MQTT).
"""

import asyncio
import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import uvicorn
from amqtt.broker import Broker
from amqtt.client import MQTTClient
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Fake OpenF1 API")
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FAKE_SESSION_KEY = "99999"


@dataclass
class Driver:
    number: int
    acronym: str
    full_name: str


SAMPLE_DRIVERS: list[Driver] = [
    Driver(1, "VER", "Max Verstappen"),
    Driver(11, "PER", "Sergio Perez"),
    Driver(44, "HAM", "Lewis Hamilton"),
    Driver(63, "RUS", "George Russell"),
    Driver(16, "LEC", "Charles Leclerc"),
    Driver(55, "SAI", "Carlos Sainz"),
    Driver(4, "NOR", "Lando Norris"),
    Driver(81, "PIA", "Oscar Piastri"),
    Driver(14, "ALO", "Fernando Alonso"),
    Driver(18, "STR", "Lance Stroll"),
]

SAMPLE_SESSION = {
    "session_key": FAKE_SESSION_KEY,
    "session_name": "Race",
    "session_type": "Race",
    "circuit_short_name": "Monza",
    "location": "Monza",
    "country_name": "Italy",
    "date_start": "2025-09-07T13:00:00",
    "date_end": "2025-09-07T15:00:00",
}


@app.post("/token")
async def get_token(username: str = Form(...), password: str = Form(...)):
    return {"access_token": "fake-token-12345", "token_type": "bearer"}


@app.get("/v1/sessions")
async def get_sessions(session_key: str | None = None):
    if session_key and session_key != FAKE_SESSION_KEY:
        return []
    return [SAMPLE_SESSION]


@app.get("/v1/drivers")
async def get_drivers(session_key: str | None = None) -> list[dict[str, Any]]:
    return [
        {
            "driver_number": d.number,
            "name_acronym": d.acronym,
            "full_name": d.full_name,
            "session_key": session_key or FAKE_SESSION_KEY,
        }
        for d in SAMPLE_DRIVERS
    ]


@app.get("/v1/position")
async def get_positions(session_key: str | None = None) -> list[dict[str, Any]]:
    positions = []
    base_time = datetime.now(timezone.utc)
    for i in range(50):
        timestamp = base_time.replace(second=i % 60).isoformat()
        for idx, driver in enumerate(SAMPLE_DRIVERS):
            pos = (idx + i) % len(SAMPLE_DRIVERS) + 1
            positions.append(
                {
                    "session_key": session_key or FAKE_SESSION_KEY,
                    "driver_number": driver.number,
                    "position": pos,
                    "date": timestamp,
                }
            )
    return positions


class DataSimulator:
    def __init__(self, session_key: str):
        self.session_key = session_key
        self.positions = {d.number: i + 1 for i, d in enumerate(SAMPLE_DRIVERS)}
        self.laps = {d.number: 1 for d in SAMPLE_DRIVERS}
        self.x_coords = {d.number: random.randint(0, 5000) for d in SAMPLE_DRIVERS}
        self.y_coords = {d.number: random.randint(0, 3000) for d in SAMPLE_DRIVERS}

    def generate_location(self, driver_number: int) -> dict:
        self.x_coords[driver_number] += random.randint(-100, 100)
        self.y_coords[driver_number] += random.randint(-50, 50)
        return {
            "session_key": self.session_key,
            "driver_number": driver_number,
            "x": self.x_coords[driver_number],
            "y": self.y_coords[driver_number],
            "z": 0,
            "date": datetime.now(timezone.utc).isoformat(),
        }

    def generate_car_data(self, driver_number: int) -> dict:
        return {
            "session_key": self.session_key,
            "driver_number": driver_number,
            "rpm": random.randint(8000, 15000),
            "speed": random.randint(150, 350),
            "n_gear": random.randint(1, 8),
            "throttle": random.randint(0, 100),
            "brake": random.randint(0, 100),
            "drs": random.choice([0, 1]),
            "date": datetime.now(timezone.utc).isoformat(),
        }

    def generate_lap(self, driver_number: int) -> dict:
        lap = self.laps[driver_number]
        self.laps[driver_number] += 1
        return {
            "session_key": self.session_key,
            "driver_number": driver_number,
            "lap_number": lap,
            "lap_duration": round(random.uniform(80.0, 95.0), 3),
            "date": datetime.now(timezone.utc).isoformat(),
        }

    def generate_interval(self, driver_number: int) -> dict:
        pos = self.positions[driver_number]
        gap = 0.0 if pos == 1 else round(random.uniform(0.5, 30.0), 3)
        return {
            "session_key": self.session_key,
            "driver_number": driver_number,
            "gap_to_leader": f"+{gap}" if pos > 1 else "LEADER",
            "interval": f"+{round(random.uniform(0.1, 5.0), 3)}",
            "date": datetime.now(timezone.utc).isoformat(),
        }

    def generate_position(self, driver_number: int) -> dict[str, Any]:
        if random.random() < 0.1:
            other = random.choice(
                [d.number for d in SAMPLE_DRIVERS if d.number != driver_number]
            )
            self.positions[driver_number], self.positions[other] = (
                self.positions[other],
                self.positions[driver_number],
            )
        return {
            "session_key": self.session_key,
            "driver_number": driver_number,
            "position": self.positions[driver_number],
            "date": datetime.now(timezone.utc).isoformat(),
        }


async def run_mqtt_broker(host: str = "0.0.0.0", port: int = 1883):
    config = {
        "listeners": {
            "default": {
                "type": "tcp",
                "bind": f"{host}:{port}",
            }
        },
        "sys_interval": 0,
        "auth": {
            "allow-anonymous": True,
        },
        "topic-check": {
            "enabled": False,
        },
    }
    broker = Broker(config)
    await broker.start()
    print(f"MQTT broker running on {host}:{port}")
    return broker


async def publish_simulator_data(host: str = "localhost", port: int = 1883):
    await asyncio.sleep(2)

    client = MQTTClient()
    await client.connect(f"mqtt://{host}:{port}")

    simulator = DataSimulator(FAKE_SESSION_KEY)
    topics = ["v1/location", "v1/laps", "v1/car_data", "v1/intervals", "v1/position"]

    print("Starting data simulator...")

    while True:
        for driver in SAMPLE_DRIVERS:
            driver_num = driver.number
            topic = random.choice(topics)

            if topic == "v1/location":
                data = simulator.generate_location(driver_num)
            elif topic == "v1/laps":
                data = simulator.generate_lap(driver_num)
            elif topic == "v1/car_data":
                data = simulator.generate_car_data(driver_num)
            elif topic == "v1/intervals":
                data = simulator.generate_interval(driver_num)
            else:
                data = simulator.generate_position(driver_num)

            payload = json.dumps(data).encode()
            await client.publish(topic, payload)

        await asyncio.sleep(0.5)


async def run_all(rest_port: int = 1221, mqtt_port: int = 1883):
    await run_mqtt_broker(port=mqtt_port)

    config = uvicorn.Config(app, host="0.0.0.0", port=rest_port, log_level="info")
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        publish_simulator_data(port=mqtt_port),
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fake OpenF1 server for testing")
    parser.add_argument("--rest-port", type=int, default=1221, help="REST API port")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT broker port")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║               Fake OpenF1 Server                             ║
╠══════════════════════════════════════════════════════════════╣
║  REST API:  http://localhost:{args.rest_port:<5}                         ║
║  MQTT:      mqtt://localhost:{args.mqtt_port:<5}                         ║
║  Session:   {FAKE_SESSION_KEY:<10}                                      ║
╠══════════════════════════════════════════════════════════════╣
║  Endpoints:                                                  ║
║    POST /token          - Get fake auth token                ║
║    GET  /v1/sessions    - Session metadata                   ║
║    GET  /v1/drivers     - Driver list                        ║
║    GET  /v1/position    - Position data                      ║
╠══════════════════════════════════════════════════════════════╣
║  MQTT Topics:                                                ║
║    v1/location, v1/laps, v1/car_data,                        ║
║    v1/intervals, v1/position                                 ║
╚══════════════════════════════════════════════════════════════╝
""")

    asyncio.run(run_all(rest_port=args.rest_port, mqtt_port=args.mqtt_port))


if __name__ == "__main__":
    main()
