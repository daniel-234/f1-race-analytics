import pytest

from f1_race_analytics.f1_data import (
    JOLPICA_ENDPOINT,
    _build_url,
    fetch_drivers_by_constructor,
    fetch_results_by_race,
)


def test_build_url_exact_match():
    url = _build_url(2026, "constructors", "red_bull", "drivers")

    assert url == f"{JOLPICA_ENDPOINT}/2026/constructors/red_bull/drivers/"


@pytest.mark.parametrize(
    "segments",
    [
        ("races",),
        ("constructors", "red_bull", "drivers"),
    ],
)
def test_build_url_no_double_slashes(segments):
    url = _build_url(2026, *segments)

    assert "//" not in url.removeprefix("https://")


def test_fetch_drivers_passes_clean_segments(monkeypatch):
    calls = []

    def fake_fetch(year, *segments):
        calls.append((year, segments))
        return None

    monkeypatch.setattr("f1_race_analytics.f1_data._fetch_data", fake_fetch)

    fetch_drivers_by_constructor(2026, "red_bull")

    assert calls == [(2026, ("constructors", "red_bull", "drivers"))]


def test_fetch_results_passes_clean_segments(monkeypatch):
    calls = []

    def fake_fetch(year, *segments):
        calls.append((year, segments))
        return None

    monkeypatch.setattr("f1_race_analytics.f1_data._fetch_data", fake_fetch)

    fetch_results_by_race(2026, "monza")

    assert calls == [(2026, ("circuits", "monza", "results"))]
