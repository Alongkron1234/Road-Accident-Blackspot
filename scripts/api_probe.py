"""
Issue 02 — prototype script ยืนยันว่าสิ่งที่บันทึกไว้ใน docs/api_notes.md ตรงกับของจริง

รันแล้วข้อมูลจะถูกเซฟลง data/raw/api_probe/ (gitignore ไว้แล้ว, ไม่ทับ docs/api_samples/
ซึ่งเป็นตัวอย่างอ้างอิงที่ commit เข้า repo)

Usage:
    python scripts/api_probe.py
"""

import csv
import io
import json
from pathlib import Path

import requests

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "api_probe"

ARMS_RESOURCES = {
    "arms_2565.json": "https://dataportal.drr.go.th/dataset/2f17d1a8-1b5c-4e0f-8a82-e44aff01ca58/resource/fb8776fb-b4b3-47fc-9d32-baaf253df9ab/download/accident.json",
    "arms_2566.csv": "https://dataportal.drr.go.th/dataset/2f17d1a8-1b5c-4e0f-8a82-e44aff01ca58/resource/db9a7d00-e4fe-4b1a-9c27-5459a122f9d0/download/2566_accident_drr.csv",
    "arms_2567.csv": "https://dataportal.drr.go.th/dataset/2f17d1a8-1b5c-4e0f-8a82-e44aff01ca58/resource/27e25ae5-0e2d-4300-bc08-325f9022b480/download/2567_accident_drr.csv",
    "arms_2568.csv": "https://dataportal.drr.go.th/dataset/2f17d1a8-1b5c-4e0f-8a82-e44aff01ca58/resource/ed8b6754-6263-4c3b-b6dc-67fefdfac0be/download/2568_accident_drr.csv",
}

EXAT_ACCIDENT_URL = "https://exat-man.web.app/api/EXAT_Accident/{year}/{month}"


def fetch(url: str) -> bytes:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content


def probe_arms():
    print("=== ARMS ===")
    for filename, url in ARMS_RESOURCES.items():
        raw = fetch(url)
        out_path = OUTPUT_DIR / filename
        out_path.write_bytes(raw)

        if filename.endswith(".json"):
            data = json.loads(raw)
            records = data[list(data.keys())[0]]
            n_missing_geo = sum(
                1 for r in records if r.get("LATITUDE") is None or r.get("LONGITUDE") is None
            )
        else:
            rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
            records = rows
            n_missing_geo = sum(1 for r in rows if not r.get("latitude") or not r.get("longitude"))

        print(f"  {filename}: {len(records)} records, {n_missing_geo} missing lat/lng -> saved to {out_path}")


def probe_exat(year: int = 2564, month: int = 1):
    print("=== EXAT ===")
    url = EXAT_ACCIDENT_URL.format(year=year, month=month)
    raw = fetch(url)
    out_path = OUTPUT_DIR / f"exat_{year}_{month:02d}.json"
    out_path.write_bytes(raw)

    data = json.loads(raw)
    records = data.get("result", [])
    has_geo_field = bool(records) and any(
        k.lower() in ("lat", "latitude", "lng", "longitude") for k in records[0]
    )
    print(f"  EXAT_Accident/{year}/{month}: {len(records)} records, has geo field: {has_geo_field} -> saved to {out_path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    probe_arms()
    probe_exat()
    print(f"\nOutput directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
