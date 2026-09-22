import json

import responses

from extract.exat_extractor import EXAT_ACCIDENT_URL, fetch_month


@responses.activate
def test_fetch_month_parses_records(exat_sample):
    url = EXAT_ACCIDENT_URL.format(year=2564, month=1)
    responses.add(responses.GET, url, body=exat_sample, status=200)

    raw, records = fetch_month(2564, 1)

    expected = json.loads(exat_sample)["result"]
    assert raw == exat_sample
    assert records == expected


@responses.activate
def test_fetch_month_empty_result_not_error():
    url = EXAT_ACCIDENT_URL.format(year=2558, month=1)
    responses.add(responses.GET, url, json={"resultCode": 0, "result": []}, status=200)

    raw, records = fetch_month(2558, 1)

    assert records == []
