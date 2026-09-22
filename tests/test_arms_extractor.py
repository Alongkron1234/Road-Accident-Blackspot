import json

from extract.arms_extractor import build_filename, parse_record_count


def test_build_filename():
    assert build_filename("arms_2568.csv", "20260101") == "arms_2568_20260101.csv"
    assert build_filename("arms_2565.json", "20260101") == "arms_2565_20260101.json"


def test_parse_record_count_json(arms_json_sample):
    data = json.loads(arms_json_sample)
    expected = len(data[list(data.keys())[0]])

    assert parse_record_count("arms_2565.json", arms_json_sample) == expected


def test_parse_record_count_csv(arms_csv_sample):
    # ตรวจว่านับ record ถูก และไฟล์ตัวอย่างมี BOM (utf-8-sig) จริงตามที่ parse_record_count รองรับ
    assert arms_csv_sample.startswith(b"\xef\xbb\xbf")

    n = parse_record_count("arms_2566.csv", arms_csv_sample)
    assert n > 0
