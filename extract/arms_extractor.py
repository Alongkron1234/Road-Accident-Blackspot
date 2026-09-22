import csv
import io
import json
from datetime import datetime
from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

ARMS_RESOURCES = {
    "arms_2565.json": "https://dataportal.drr.go.th/dataset/2f17d1a8-1b5c-4e0f-8a82-e44aff01ca58/resource/fb8776fb-b4b3-47fc-9d32-baaf253df9ab/download/accident.json",
    "arms_2566.csv": "https://dataportal.drr.go.th/dataset/2f17d1a8-1b5c-4e0f-8a82-e44aff01ca58/resource/db9a7d00-e4fe-4b1a-9c27-5459a122f9d0/download/2566_accident_drr.csv",
    "arms_2567.csv": "https://dataportal.drr.go.th/dataset/2f17d1a8-1b5c-4e0f-8a82-e44aff01ca58/resource/27e25ae5-0e2d-4300-bc08-325f9022b480/download/2567_accident_drr.csv",
    "arms_2568.csv": "https://dataportal.drr.go.th/dataset/2f17d1a8-1b5c-4e0f-8a82-e44aff01ca58/resource/ed8b6754-6263-4c3b-b6dc-67fefdfac0be/download/2568_accident_drr.csv",
}


@retry(reraise=True, stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=10))
def fetch(url: str) -> bytes:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content


def build_filename(resource_filename: str, ts: str) -> str:
    stem, ext = resource_filename.rsplit(".", 1)
    return f"{stem}_{ts}.{ext}"


def parse_record_count(filename: str, raw: bytes) -> int:
    if filename.endswith(".json"):
        data = json.loads(raw)
        return len(data[list(data.keys())[0]])
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    return len(rows)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d")

    print("=== ARMS ===")
    total = 0
    for filename, url in ARMS_RESOURCES.items():
        raw = fetch(url)
        out_path = OUTPUT_DIR / build_filename(filename, ts)
        out_path.write_bytes(raw)

        n = parse_record_count(filename, raw)
        total += n
        print(f"  {filename}: {n} records -> saved to {out_path}")

    print(f"\nTotal ARMS records: {total}")


if __name__ == "__main__":
    main()
