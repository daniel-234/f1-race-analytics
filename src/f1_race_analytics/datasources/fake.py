import asyncio
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from .base import Position, RaceDataSource


class RaceSimulator:
    """
    Simulates a live race by randomly swapping adjacent driver positions.
    State is shared across all requests so positions evolve over time.
    """

    def __init__(self, drivers: list[dict], total_laps: int = 58):
        self.drivers = drivers
        self.total_laps = total_laps
        self.current_lap = 1
        self.last_update = datetime.now(timezone.utc)
        self.positions = [d["driver_name"] for d in drivers]
        self.previous_positions = list(self.positions)
        # Build a lookup map for quick access
        self.driver_info = {d["driver_name"]: d for d in drivers}

    def get_positions(self) -> list[Position]:
        self._tick()
        return [
            Position(
                driver_name=name,
                driver_number=self.driver_info[name]["driver_number"],
                position=idx + 1,
                change=(self.previous_positions.index(name) + 1) - (idx + 1),
            )
            for idx, name in enumerate(self.positions)
        ]

    def is_finished(self) -> bool:
        return self.current_lap >= self.total_laps

    def get_drivers(self) -> list[dict]:
        return self.drivers

    def _tick(self):
        now = datetime.now(timezone.utc)
        elapsed = (now - self.last_update).total_seconds()
        # Change it to 15 to resemble the API update time
        if elapsed >= 3:
            self._simulate_position_changes()
            self._advance_lap()
            self.last_update = now

    def _simulate_position_changes(self):
        self.previous_positions = list(self.positions)
        num_swaps = random.randint(0, 3)
        for _ in range(num_swaps):
            idx = random.randint(0, len(self.positions) - 2)
            self.positions[idx], self.positions[idx + 1] = (
                self.positions[idx + 1],
                self.positions[idx],
            )

    def _advance_lap(self):
        if self.current_lap < self.total_laps:
            self.current_lap += 1


class FakeDataSource(RaceDataSource):
    """Replay recorded JSON data with configurable delay (for dev/testing)"""

    def __init__(self, data_file: Path, delay_ms: int = 100):
        self.delay_ms = delay_ms
        drivers = self._load_drivers(data_file)
        self.simulator = RaceSimulator(drivers=drivers)

    def _load_drivers(self, data_file: Path) -> list[dict]:
        with open(data_file) as f:
            data = json.load(f)
        return data["drivers"]

    def is_finished(self) -> bool:
        return self.simulator.is_finished()

    async def get_positions(self, fixture_id: str) -> list[Position]:
        await asyncio.sleep(self.delay_ms / 1000)
        return self.simulator.get_positions()

    async def get_drivers(self, fixture_id: str) -> list[dict]:
        await asyncio.sleep(self.delay_ms / 1000)
        return self.simulator.get_drivers()
