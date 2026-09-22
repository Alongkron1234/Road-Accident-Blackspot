from pathlib import Path

import pytest

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "docs" / "api_samples"


@pytest.fixture
def arms_json_sample() -> bytes:
    return (SAMPLES_DIR / "arms_accident_sample.json").read_bytes()


@pytest.fixture
def arms_csv_sample() -> bytes:
    return (SAMPLES_DIR / "arms_2566_sample.csv").read_bytes()


@pytest.fixture
def exat_sample() -> bytes:
    return (SAMPLES_DIR / "exat_accident_sample.json").read_bytes()
