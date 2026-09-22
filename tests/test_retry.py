import pytest
import responses
from tenacity import wait_none

from extract import arms_extractor, exat_extractor

URL = "https://example.test/resource"


@pytest.fixture(autouse=True)
def no_wait_between_retries():
    # ปกติ fetch() รอ exponential backoff จริง (~1s, 2s, 4s...) ทำให้ test ช้ามาก
    # override เป็น wait_none() เฉพาะตอนรัน test นี้ แล้วคืนค่าเดิมหลังจบ
    arms_original = arms_extractor.fetch.retry.wait
    exat_original = exat_extractor.fetch.retry.wait
    arms_extractor.fetch.retry.wait = wait_none()
    exat_extractor.fetch.retry.wait = wait_none()
    yield
    arms_extractor.fetch.retry.wait = arms_original
    exat_extractor.fetch.retry.wait = exat_original


@responses.activate
def test_fetch_retries_on_500_then_succeeds():
    responses.add(responses.GET, URL, status=500)
    responses.add(responses.GET, URL, body=b"ok", status=200)

    result = arms_extractor.fetch(URL)

    assert result == b"ok"
    assert len(responses.calls) == 2


@responses.activate
def test_fetch_raises_after_exhausting_retries():
    for _ in range(4):
        responses.add(responses.GET, URL, status=500)

    with pytest.raises(Exception):
        exat_extractor.fetch(URL)

    assert len(responses.calls) == 4
