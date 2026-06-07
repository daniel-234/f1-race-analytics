import pytest

from f1_race_analytics.f1_data import JOLPICA_ENDPOINT, _build_url


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
