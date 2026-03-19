from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Position:
    driver_name: str
    driver_number: int
    position: int
    change: int = 0
    cumulative_change: int = 0


class RaceDataSource(ABC):
    @abstractmethod
    async def get_positions(self, fixture_id: str) -> list[Position]:
        """Fetch current positions."""
        ...

    @abstractmethod
    async def get_drivers(self, fixture_id: str) -> list[dict]:
        """Fetch drivers and additional info for a session."""
        ...

    @abstractmethod
    def is_finished(self) -> bool:
        """Return True when the session is over."""
        ...
