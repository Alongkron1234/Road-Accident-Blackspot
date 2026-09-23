"""
Issue 05 — อ่านไฟล์ดิบใน data/raw/ (จาก Issue 04) แล้ว insert เข้า raw_arms/raw_exat
ใน Postgres แบบ idempotent (รันซ้ำไฟล์เดิมไม่ insert ซ้ำ)

ไม่แปลง/ทำความสะอาดข้อมูลใดๆ ทั้งสิ้น (ตาม pattern ELT) — payload เก็บ list ของ record
ดิบทั้งไฟล์เป็น JSONB array เดียว, 1 แถว = 1 ไฟล์

Usage:
    python extract/loader.py
"""

import csv
import io
import json
import re
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

ARMS_FILENAME_RE = re.compile(r"^arms_(?P<year>\d{4})_\d{8}\.(?P<ext>json|csv)$")
EXAT_FILENAME_RE = re.compile(r"^exat_(?P<year>\d{4})_(?P<month>\d{2})_\d{8}\.json$")


def get_connection():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["WAREHOUSE_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def parse_arms_records(raw: bytes, ext: str) -> list:
    if ext == "json":
        data = json.loads(raw)
        return data[list(data.keys())[0]]
    rows = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    return list(rows)


def load_arms_files(conn) -> tuple[int, int]:
    inserted, skipped = 0, 0
    for path in sorted(RAW_DIR.glob("arms_*.*")):
        match = ARMS_FILENAME_RE.match(path.name)
        if not match:
            continue

        raw = path.read_bytes()
        records = parse_arms_records(raw, match["ext"])

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO raw_arms (source_file, source_format, source_year, payload)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source_file) DO NOTHING
                """,
                (path.name, match["ext"], match["year"], json.dumps(records)),
            )
            if cur.rowcount == 1:
                inserted += 1
                print(f"  inserted: {path.name} ({len(records)} records)")
            else:
                skipped += 1
                print(f"  skipped (already loaded): {path.name}")

    return inserted, skipped


def load_exat_files(conn) -> tuple[int, int]:
    inserted, skipped = 0, 0
    for path in sorted(RAW_DIR.glob("exat_*.json")):
        match = EXAT_FILENAME_RE.match(path.name)
        if not match:
            continue

        raw = path.read_bytes()
        records = json.loads(raw).get("result", [])

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO raw_exat (source_file, source_year, source_month, payload)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source_file) DO NOTHING
                """,
                (path.name, match["year"], match["month"], json.dumps(records)),
            )
            if cur.rowcount == 1:
                inserted += 1
                print(f"  inserted: {path.name} ({len(records)} records)")
            else:
                skipped += 1
                print(f"  skipped (already loaded): {path.name}")

    return inserted, skipped


def main():
    conn = get_connection()
    try:
        print("=== ARMS ===")
        arms_inserted, arms_skipped = load_arms_files(conn)

        print("=== EXAT ===")
        exat_inserted, exat_skipped = load_exat_files(conn)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(
        f"\nARMS: {arms_inserted} inserted, {arms_skipped} skipped | "
        f"EXAT: {exat_inserted} inserted, {exat_skipped} skipped"
    )


if __name__ == "__main__":
    main()
