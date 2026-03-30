from .base import Position, RaceDataSource


class SportmonksDataSource(RaceDataSource):
    async def get_positions(self, fixture_id: str) -> list[Position]:
        raise NotImplementedError

    async def get_drivers(self, fixture_id: str) -> list[dict]:
        raise NotImplementedError

    def is_finished(self) -> bool:
        raise NotImplementedError
