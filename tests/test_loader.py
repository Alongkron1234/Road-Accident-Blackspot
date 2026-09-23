import json

import pytest

from extract import loader


@pytest.fixture
def db_conn():
    try:
        conn = loader.get_connection()
    except Exception as e:
        pytest.skip(f"ต่อ Postgres ทดสอบไม่ได้ (ต้องรัน docker compose up ก่อน): {e}")
    yield conn
    # rollback แทน commit เสมอ กัน test เขียนข้อมูลปนกับข้อมูลจริงใน raw_arms/raw_exat
    conn.rollback()
    conn.close()


def test_parse_arms_records_json(arms_json_sample):
    records = loader.parse_arms_records(arms_json_sample, "json")

    data = json.loads(arms_json_sample)
    assert records == data[list(data.keys())[0]]


def test_parse_arms_records_csv(arms_csv_sample):
    records = loader.parse_arms_records(arms_csv_sample, "csv")

    assert len(records) > 0
    assert isinstance(records[0], dict)


def test_load_arms_files_inserts_and_skips_duplicate(db_conn, monkeypatch, tmp_path):
    fixture_file = tmp_path / "arms_9999_20260101.json"
    fixture_file.write_text(json.dumps({"some query": [{"ID": 1, "LATITUDE": 13.7}]}))
    monkeypatch.setattr(loader, "RAW_DIR", tmp_path)

    inserted, skipped = loader.load_arms_files(db_conn)
    assert (inserted, skipped) == (1, 0)

    # รันซ้ำไฟล์เดิม (ในทรานแซคชันเดียวกัน) ต้อง skip ไม่ insert ซ้ำ
    inserted_again, skipped_again = loader.load_arms_files(db_conn)
    assert (inserted_again, skipped_again) == (0, 1)


def test_load_exat_files_inserts(db_conn, monkeypatch, tmp_path):
    fixture_file = tmp_path / "exat_9999_01_20260101.json"
    fixture_file.write_text(json.dumps({"resultCode": 0, "result": [{"_id": 1}]}))
    monkeypatch.setattr(loader, "RAW_DIR", tmp_path)

    inserted, skipped = loader.load_exat_files(db_conn)
    assert (inserted, skipped) == (1, 0)
