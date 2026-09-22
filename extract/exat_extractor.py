import json
from datetime import datetime
from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

EXAT_ACCIDENT_URL = "https://exat-man.web.app/api/EXAT_Accident/{year}/{month}"

# ค้นพบจาก scripts/exat_year_probe.py — พ.ศ. 2558-2569 มีข้อมูลจริงหมด
EXAT_YEARS = range(2558, 2570)


@retry(reraise=True, stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=10))
def fetch(url: str) -> bytes:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content

# รับ input เดือน/ปี แล้วทำเป็น url ส่งให้ fetch ไปดึงข้อมูล
def fetch_month(year: int, month: int) -> tuple[bytes, list]:
    url = EXAT_ACCIDENT_URL.format(year=year, month=month)
    raw = fetch(url)
    data = json.loads(raw)
    records = data.get("result", [])
    return raw, records


def save_month(year: int, month: int, raw: bytes, ts: str) -> Path:
    out_path = OUTPUT_DIR / f"exat_{year}_{month:02d}_{ts}.json"
    out_path.write_bytes(raw)
    return out_path


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d")

    print("=== EXAT ===")
    total = 0
    for year in EXAT_YEARS:
        for month in range(1, 13):
            raw, records = fetch_month(year, month)
            out_path = save_month(year, month, raw, ts)
            n = len(records)
            total += n
            print(f"  {year}/{month:02d}: {n} records -> saved to {out_path}")

    print(f"\nTotal EXAT records: {total}")


if __name__ == "__main__":
    main()
