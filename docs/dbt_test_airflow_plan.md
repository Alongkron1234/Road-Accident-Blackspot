# แผนผูก `dbt test` เข้า Airflow DAG (Issue 10 step 5, ทำจริงใน Issue 12)

## ลำดับ task ที่วางแผนไว้

```
[extract_arms, extract_exat] >> load_raw >> dbt_run >> dbt_test >> generate_map >> publish_map
```

ต่อจาก `extract_load_dag` ที่มีอยู่แล้ว (Issue 06) เพิ่ม 4 task ใหม่ต่อท้าย `load_raw`:
- `dbt_run` — เรียก `dbt run` (สร้าง/อัปเดต staging → intermediate → mart)
- `dbt_test` — เรียก `dbt test` (เช็คคุณภาพข้อมูลทุก layer)
- `generate_map` — สร้างแผนที่ (Issue 11, `scripts/generate_map.py`)
- `publish_map` — publish ขึ้น GitHub Pages (Issue 11)

## ทำไม `dbt_test` fail แล้ว `generate_map`/`publish_map` จะไม่รันเองโดยอัตโนมัติ

**ไม่ต้องตั้งค่าอะไรเพิ่มเลย** — เป็นพฤติกรรม default ของ Airflow (`trigger_rule='all_success'`
เป็นค่าเริ่มต้นของทุก task อยู่แล้ว) พิสูจน์ให้เห็นแล้วจริงตอน Issue 06: ตอนจงใจทำ `extract_arms`
fail เพื่อทดสอบ retry, `load_raw` ที่อยู่ downstream ไม่ได้รันเลย ขึ้นสถานะ `upstream_failed`
ทันที — หลักการเดียวกันจะใช้ได้กับ `dbt_test` → `generate_map` โดยไม่ต้องเขียนโค้ดเพิ่ม

## รูปแบบ task ที่จะใช้ (คร่าวๆ ยังไม่ implement จริงจนกว่าจะถึง Issue 12)

`dbt_run`/`dbt_test` น่าจะใช้ `BashOperator` เรียก `dbt run --project-dir dbt --profiles-dir dbt`
ตรงๆ (ต่างจาก `extract_arms`/`load_raw` ที่ใช้ `PythonOperator` เรียก Python function เพราะ dbt
เป็นคำสั่ง CLI ไม่ใช่ Python module ที่ import ได้ตรงๆ) — ต้องมี `dbt` ติดตั้งอยู่ใน Airflow
container ด้วย (ปัจจุบันติดตั้งผ่าน `_PIP_ADDITIONAL_REQUIREMENTS` เหมือน `tenacity`/`psycopg2`
ที่ทำไว้ตอน Issue 06 — ต้องเพิ่ม `dbt-core`/`dbt-postgres` เข้าไปด้วยตอนถึง Issue 12)

## สิ่งที่ยังไม่ตัดสินใจ (รอ Issue 12)

- จะ mount โฟลเดอร์ `dbt/` เข้า Airflow container ยังไง (เหมือนที่ mount `extract/` ไว้ใน Issue 06)
- `retries`/`retry_delay` ของ `dbt_run`/`dbt_test` ควรต่างจาก `extract_*` ไหม (dbt ไม่ได้ยิง API
  ภายนอกที่ไม่เสถียร เหตุผลของ retry อาจไม่จำเป็นเท่า extractor)
