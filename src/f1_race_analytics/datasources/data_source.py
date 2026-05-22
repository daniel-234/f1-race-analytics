from pathlib import Path

from decouple import config

from .base import RaceDataSource
from .fake import FakeDataSource
from .sportmonks import SportmonksDataSource

# points to f1_race_analytics/
BASE_DIR = Path(__file__).resolve().parent.parent


def get_data_source() -> RaceDataSource:
    source_type = config("DATA_SOURCE", default="fake")

    if source_type == "fake":
        return FakeDataSource(
            data_file=BASE_DIR / "data" / "replay.json",
            delay_ms=config("FAKE_DELAY_MS", default=100, cast=int),
        )
    elif source_type == "sportmonks":
        return SportmonksDataSource()
    else:
        raise ValueError(f"Unknown data source: {source_type}")
