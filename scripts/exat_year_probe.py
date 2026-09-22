import requests

EXAT_ACCIDENT_URL = "https://exat-man.web.app/api/EXAT_Accident/{year}/{month}"

CANDIDATE_YEARS_BE = range(2558, 2570)  # ~CE 2015-2026
CHECK_MONTHS = (1, 6)


def probe_month(year: int, month: int) -> int | None:
    url = EXAT_ACCIDENT_URL.format(year=year, month=month)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        return None
    data = resp.json()
    return len(data.get("result", []))


def main():
    print(f"{'ปี พ.ศ.':<10}{'เดือน 1':<12}{'เดือน 6':<12}สถานะ")
    for year in CANDIDATE_YEARS_BE:
        counts = {m: probe_month(year, m) for m in CHECK_MONTHS}

        if all(c is None for c in counts.values()):
            status = "error/ไม่รองรับ"
        elif all(c == 0 for c in counts.values()):
            status = "valid-empty (สงสัยว่าไม่รองรับ หรือไม่มีข้อมูลจริง)"
        else:
            status = "valid-with-data"

        m1 = "error" if counts[1] is None else counts[1]
        m6 = "error" if counts[6] is None else counts[6]
        print(f"{year:<10}{m1:<12}{m6:<12}{status}")


if __name__ == "__main__":
    main()
