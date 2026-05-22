from .base import Position, RaceDataSource


class SportmonksDataSource(RaceDataSource):
    def __init__(self):
        raise NotImplementedError(
            "SportmonksDataSource is not implemented yet. "
            "Set DATA_SOURCE=fake in your .env"
        )

    async def get_positions(self, fixture_id: str) -> list[Position]:
        raise NotImplementedError

    async def get_drivers(self, fixture_id: str) -> list[dict]:
        raise NotImplementedError

    def is_finished(self) -> bool:
        raise NotImplementedError
