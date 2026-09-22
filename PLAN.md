# Road Accident Blackspot Pipeline — แผนงานทั้งโครงงาน

## กลยุทธ์ branch

- `main` = branch หลัก, protect ไว้, merge ผ่าน PR เท่านั้น
- ทุก Issue = 1 feature branch ตั้งชื่อ `feat/<เลข issue>-<slug>` เช่น `feat/01-repo-scaffold`
- แต่ละ branch จบงานแล้ว merge กลับ `main` ก่อนเริ่ม branch ถัดไป (งานเรียงเป็น dependency chain เป็นส่วนใหญ่)
- Commit เล็กๆ บ่อยๆ ใน branch ได้ ไม่ต้อง squash ถ้าไม่อยากทำ

Dependency คร่าวๆ: `01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11`, ส่วน `12/13` (REST API, LINE bot) เป็น optional ทำหลัง 11 เสร็จก็ได้ ไม่บล็อกอะไร

---

## ตาราง Issue รวม

| # | Issue | Branch | ต้องรอ |
|---|---|---|---|
| 01 | Repo scaffold + dev environment | `feat/01-repo-scaffold` | - |
| 02 | สำรวจ/ทดสอบ API จริง (ARMS, EXAT) | `feat/02-api-exploration` | 01 |
| 03 | Docker Compose: Postgres + Airflow | `feat/03-infra-postgres-airflow` | 01 |
| 04 | Extract scripts (ARMS, EXAT) | `feat/04-extract-scripts` | 02, 03 |
| 05 | Load raw layer เข้า Postgres | `feat/05-load-raw-layer` | 04 |
| 06 | Airflow DAG: extract → load (รันจริงได้) | `feat/06-airflow-extract-load-dag` | 05 |
| 07 | dbt project setup + staging layer | `feat/07-dbt-staging` | 06 |
| 08 | dbt clustering layer (DBSCAN) | `feat/08-dbt-clustering` | 07 |
| 09 | dbt mart layer (severity score) | `feat/09-dbt-mart` | 08 |
| 10 | dbt tests (data quality gate) | `feat/10-dbt-tests` | 09 |
| 11 | Folium map + publish ขึ้น GitHub Pages | `feat/11-publish-map` | 10 |
| 12 | ผูก dbt run + publish เข้า Airflow DAG (end-to-end) | `feat/12-full-dag-integration` | 11 |
| 13 | README + เอกสารโครงงาน + finalize | `feat/13-docs-finalize` | 12 |
| 14* | (Optional) REST API เผยแพร่ blackspot data | `feat/14-rest-api` | 12 |
| 15* | (Optional) LINE Bot แจ้งเตือนจุดเสี่ยง | `feat/15-line-bot` | 14 |

---

## Issue 01 — Repo scaffold + dev environment

**เป้าหมาย:** มีโครงสร้างโปรเจกต์ที่ทุก issue ถัดไปต่อยอดได้ พร้อม tooling พื้นฐาน

**ขั้นตอน:**
1. `git init`, สร้าง repo บน GitHub (private หรือ public ก็ได้ตามต้องการ), ตั้ง remote
2. สร้างโครงสร้างโฟลเดอร์:
   ```
   ├── airflow/
   │   └── dags/
   ├── dbt/
   ├── extract/          # python extract scripts
   ├── scripts/          # helper scripts (publish, etc.)
   ├── docs/
   ├── .github/
   ├── docker-compose.yml
   ├── .env.example
   ├── .gitignore
   ├── requirements.txt / pyproject.toml
   └── README.md (สั้นๆ ก่อน ค่อยเติมทีหลังใน issue 13)
   ```
3. ตั้ง Python version (แนะนำ 3.11) ด้วย `pyenv` หรือ `venv`, สร้าง `requirements.txt` เปล่าไว้ก่อน
4. เพิ่ม `.gitignore` (python, airflow logs, `.env`, `__pycache__`, dbt `target/`, `logs/`)
5. ตั้งค่า pre-commit เบื้องต้น (ruff/black) — ไม่บังคับ แต่ช่วยคุณภาพโค้ด
6. เปิด branch protection บน `main` (require PR review หรืออย่างน้อย require PR ก่อน merge)
7. Commit, push, เปิด PR แรก, merge เข้า `main`

**Definition of Done:** repo อยู่บน GitHub, mainprotected, โครงสร้างโฟลเดอร์พร้อม, README ตัวต้นแบบ

---

## Issue 02 — สำรวจ/ทดสอบ API จริง (ARMS, EXAT) ✅ เสร็จแล้ว

**เป้าหมาย:** เข้าใจ response จริงของทั้งสอง API ก่อนเขียนโค้ด (field, pagination, auth, rate limit, edge case)

**ขั้นตอน:**
1. เข้า datagov.mot.go.th หา endpoint ของ `arms_accident` และ `exat-accident`, สมัคร API key ถ้าต้องใช้
2. ยิง request ทดสอบด้วย `curl`/Postman เก็บ response ตัวอย่างไว้ใน `docs/api_samples/arms_sample.json` และ `exat_sample.json`
3. บันทึกลง `docs/api_notes.md`:
   - Base URL, method, auth header/query param ที่ต้องใช้
   - Field ทั้งหมดที่มี พร้อม type และความหมาย (ชื่อถนน, lat/lng, วันเวลา, ความรุนแรง, ฯลฯ)
   - Pagination (limit/offset หรือ page-based), มี rate limit ไหม
   - ความถี่ที่ข้อมูลอัปเดตจริง (real-time vs รายเดือนตามที่ระบุไว้)
   - Field ไหนที่ชื่อไม่ตรงกันระหว่างสอง source (เตรียมไว้สำหรับ mapping ใน staging layer)
   - เคส edge: พิกัดเป็น null, พิกัด (0,0), format วันที่ต่างกัน
4. เขียน prototype script สั้นๆ (`scripts/api_probe.py`) ดึงข้อมูลจริงมาดู ไม่ต้อง production-grade

**Definition of Done:** มี `docs/api_notes.md` ที่ครบถ้วนพอจะเขียน extract script ได้โดยไม่ต้องเดา, มี sample response เก็บไว้อ้างอิง

### สิ่งที่เจอจริง (สำคัญ กระทบ Issue 04-09 ด้านล่าง — รายละเอียดเต็มดูที่ `docs/api_notes.md`)

- **ARMS ไม่ใช่ 1 resource แต่มี 4 resource แยกกัน:** `accident.json` (~209 record, ปีงบ 2565) +
  `2566_accident_drr.csv` (1,090) + `2567_accident_drr.csv` (970) + `2568_accident_drr.csv` (814)
  รวม ~3,083 record มีพิกัดครบทุกตัว **แต่ JSON กับ CSV เป็นคนละ schema กัน**
  (field ชื่อ, ตัวพิมพ์ใหญ่/เล็ก, format วันที่ต่างกันหมด)
- **EXAT เป็น REST API จริง** (`/api/EXAT_Accident/{ปี พ.ศ.}/{เดือน}`) แต่ **ไม่มีพิกัดเลย**
  มีแค่ `expw_step` เป็นชื่อทางด่วน/ช่วงทางเป็น text — เช็คครบทุก endpoint ของ EXAT แล้ว
  (`EXAT_Crash`, `EXAT_Plaza`, `EXAT_TrafficStatByPlaza/ByCar` ฯลฯ) ไม่มีตัวไหนให้พิกัดมาเลย
- **ตัดสินใจแล้ว:** ฝั่ง EXAT จะ **geocode เอง** ด้วย manual lookup table (`expw_step` → พิกัดตัวแทน
  ของทางด่วนสายนั้น) ไม่ตัด EXAT ออกจาก pipeline แต่ต้องยอมรับว่า cluster ฝั่งนี้จะหยาบกว่า ARMS มาก
- **`accident-summary-month`** เป็นแค่สถิติสรุปรายเดือน ไม่มีตำแหน่งจุดเกิดเหตุ → **ตัดออกจาก
  pipeline หลัก** ไม่ใช้ทำ blackspot (ใช้ validate ตัวเลขได้เท่านั้นถ้าต้องการ)

---

## Issue 03 — Docker Compose: Postgres + Airflow

**เป้าหมาย:** รัน Postgres + Airflow ได้บนเครื่อง local ด้วยคำสั่งเดียว

**ขั้นตอน:**
1. เขียน `docker-compose.yml` ประกอบด้วย service: `postgres` (เก็บทั้ง raw/staging/mart data), `airflow-webserver`, `airflow-scheduler`, `airflow-init` (ใช้ image ทางการของ Apache Airflow, LocalExecutor พอสำหรับโปรเจกต์นี้)
2. ตั้งค่า volume mount สำหรับ `airflow/dags` ให้ sync กับโฟลเดอร์ dev
3. สร้าง `.env.example` ระบุ env var ที่ต้องใช้ (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `AIRFLOW_UID` ฯลฯ) — ห้าม commit `.env` จริง
4. `docker compose up -d`, เช็คว่า Airflow UI เข้าได้ที่ `localhost:8080`, login ด้วย default admin
5. เช็คว่า connect เข้า Postgres จาก host ได้ (`psql` หรือ DBeaver) เพื่อ debug ระหว่างพัฒนา
6. เพิ่ม Airflow Connection สำหรับ Postgres ผ่าน UI หรือ `airflow connections add` (เตรียมไว้ใช้ใน DAG ถัดไป)
7. เขียน `docs/local_setup.md` อธิบายขั้นตอน run ให้คนอื่น (หรือตัวเองในอนาคต) ทำตามได้

**Definition of Done:** `docker compose up` แล้วเข้า Airflow UI + Postgres ได้จริง, มีเอกสาร setup

---

## Issue 04 — Extract scripts (ARMS, EXAT)

**เป้าหมาย:** ได้ Python script ที่ดึงข้อมูลจากทั้งสอง source แล้วเซฟเป็นไฟล์ดิบ พร้อม retry logic

**ขั้นตอน:**
1. สร้าง `extract/arms_extractor.py` และ `extract/exat_extractor.py` (แยกไฟล์ชัดเจน เพราะพฤติกรรม
   การดึงต่างกันมาก ไม่ควรฝืนใช้ base class ร่วม)
2. **ARMS:** ไม่มี pagination — ดึงทีละไฟล์จากทั้ง 4 resource URL ที่บันทึกไว้ใน `docs/api_notes.md`
   (1 JSON + 3 CSV แยกปีงบประมาณ 2565/2566/2567/2568) เซฟแยกไฟล์ตาม resource เดิม
   อย่ารวมเป็นไฟล์เดียวตอน extract (รวม/map schema ค่อยทำใน Issue 07 ฝั่ง dbt)
3. **EXAT:** ไม่มี pagination แบบ page number — endpoint เป็น `/{ปี พ.ศ.}/{เดือน}` ต้อง **loop ปี × เดือน (1-12)**
   จนกว่าจะได้ครบทุกเดือนที่มีข้อมูล (เดือนไหนไม่มีข้อมูลน่าจะได้ result ว่าง ไม่ error — ต้อง handle เคสนี้)
   ดึงเฉพาะ `EXAT_Accident` endpoint พอ (ไม่ต้องดึง `EXAT_Crash`/`EXAT_TrafficStat*` เพราะไม่เกี่ยวกับ blackspot)
   ก่อนเขียน loop เต็ม ควรลองไล่ปีอื่นนอกจาก 2564 ดูก่อนว่า API accept ปีไหนบ้าง (ยังไม่เคยเช็ค)
4. ใช้ `requests` (ติดตั้งแล้วใน `requirements.txt` จาก Issue 02) + retry (เช่น `tenacity` หรือ manual
   retry with backoff) รองรับกรณี API รัฐ timeout/500 — **หมายเหตุ:** ถ้า dev บนเครื่องที่ Python
   ไม่ผูก system cert store (เจอปัญหานี้ตอนทำ `api_probe.py`) ต้องใช้ `requests` ไม่ใช่ `urllib` ตรงๆ
5. เซฟผลลัพธ์เป็นไฟล์ดิบ พร้อม timestamp ในชื่อไฟล์ เช่น `data/raw/arms_2568_20260101.csv`,
   `data/raw/exat_2564_01_20260101.json` (โฟลเดอร์นี้อยู่ใน `.gitignore` ไม่ commit ข้อมูลจริง)
6. เขียน unit test เบื้องต้น (mock HTTP response) เช็ค parsing/retry logic ทำงานถูกต้อง — ใช้ `pytest` + `responses`/`unittest.mock`
7. รัน script จริงกับ API จริงหนึ่งรอบ ยืนยันว่าได้ข้อมูลจริงและไฟล์ถูกต้อง (เทียบจำนวน record กับที่บันทึกไว้ใน Issue 02)

**Definition of Done:** รัน `python extract/arms_extractor.py` และ `exat_extractor.py` แล้วได้ไฟล์ดิบจริงครบทุก resource/เดือน, มี test ผ่าน, มี retry ที่ทดสอบแล้วว่าทำงาน

---

## Issue 05 — Load raw layer เข้า Postgres

**เป้าหมาย:** โหลด JSON ดิบเข้า Postgres เป็น `raw_arms`, `raw_exat` โดยไม่แปลงข้อมูล (ตาม ELT)

**ขั้นตอน:**
1. ออกแบบ schema ตาราง raw: เก็บเป็น `JSONB` column (เช่น `payload jsonb`, `source_file text`, `loaded_at timestamptz`, `id serial`) — ให้ยืดหยุ่นรองรับ schema เปลี่ยนแปลงจาก API ได้
   เพิ่ม column `source_format` (`json`/`csv`) และ `source_year` ด้วย เพราะ ARMS มี 2 schema ปนกัน
   ในตารางเดียว (JSON export กับ CSV export field ไม่เหมือนกัน ตามที่พบใน Issue 02) การมี column
   นี้ช่วย debug ย้อนหลังว่า record ไหนมาจาก resource ไหน โดยไม่ต้องเดาจากเนื้อหา JSONB เอง
2. เขียน SQL migration หรือ `CREATE TABLE IF NOT EXISTS` script ใน `dbt/` (เป็น seed/pre-hook) หรือแยกเป็น `scripts/init_db.sql`
3. เขียน `extract/loader.py` อ่านไฟล์ดิบ (รองรับทั้ง JSON และ CSV จาก ARMS, JSON จาก EXAT) →
   insert เข้า `raw_arms`/`raw_exat` ผ่าน `psycopg2`/`sqlalchemy` (CSV ต้อง parse เป็น dict ก่อนแปลง
   เป็น JSONB เก็บ เพื่อให้ทั้งตาราง query แบบ JSONB ได้เหมือนกันหมด)
4. ทำ idempotency: ถ้ารันซ้ำไฟล์เดิมไม่ควร insert ซ้ำ (เช่น unique constraint บน `source_file` หรือ upsert logic)
5. Test: รัน loader กับไฟล์ sample จาก issue 02/04 แล้ว query ยืนยันข้อมูลอยู่ใน Postgres ถูกต้อง
6. เขียน unit test สำหรับ loader (ใช้ test database หรือ testcontainers ถ้าสะดวก)

**Definition of Done:** รัน extractor แล้วต่อด้วย loader ได้ข้อมูลจริงอยู่ใน `raw_arms`/`raw_exat` ใน Postgres, รันซ้ำไม่ insert ซ้ำ

---

## Issue 06 — Airflow DAG: extract → load (รันจริงได้)

**เป้าหมาย:** ผูก extract + load เข้า Airflow DAG ที่รันอัตโนมัติได้จริง พร้อม parallel task และ retry

**ขั้นตอน:**
1. สร้าง `airflow/dags/extract_load_dag.py`
2. ออกแบบ DAG: 2 task ขนาน (`extract_arms`, `extract_exat`) → ต่อด้วย `load_arms`, `load_exat` (หรือรวม load เป็น task เดียวที่ loop ทั้งสอง source ก็ได้ ให้เลือกแบบที่ debug ง่ายกว่า)
3. ตั้ง `retries`, `retry_delay` ระดับ task ตาม requirement (รองรับ API รัฐไม่เสถียร)
4. ตั้ง schedule `@daily`
5. ใช้ `PythonOperator` เรียก extractor/loader ที่เขียนไว้ใน issue 04/05 (import เป็น module ไม่ copy-paste โค้ด)
6. Trigger DAG manual ผ่าน Airflow UI ทดสอบว่ารันจบสำเร็จ, เช็ค log แต่ละ task
7. ทดสอบ failure case: ปิดเน็ต/mock error ชั่วคราว ดูว่า retry ทำงานตามที่ตั้งไว้

**Definition of Done:** Trigger DAG จาก Airflow UI แล้ววิ่งจบสำเร็จ ข้อมูลจริงไหลเข้า Postgres, retry ทำงานได้จริงเมื่อ mock failure

---

## Issue 07 — dbt project setup + staging layer

**เป้าหมาย:** ตั้ง dbt project เชื่อม Postgres ได้ และมี `stg_accidents` schema เดียวกันจากทั้ง 3 schema ต้นทาง

⚠️ **ปรับจากแผนเดิม:** ตอนแรกคิดว่ามีแค่ 2 source (ARMS, EXAT) แต่ ARMS เองมี 2 schema ย่อยปนกัน
(JSON export กับ CSV export field/format ไม่เหมือนกัน) รวมเป็น **3 schema ที่ต้อง map เข้าด้วยกัน**
และฝั่ง EXAT ไม่มีพิกัดมาเอง ต้อง geocode ก่อนถึงจะเข้า staging ได้

**ขั้นตอน:**
1. `dbt init` ใน `dbt/`, ตั้งค่า `profiles.yml` ชี้ไป Postgres ใน docker-compose (ใช้ env var ผ่าน `env_var()` ไม่ hardcode credential)
2. `dbt debug` ยืนยัน connection ผ่าน
3. เขียน dbt source definition ชี้ไปตาราง `raw_arms`, `raw_exat`
4. สร้าง **seed** `dbt/seeds/expw_step_coordinates.csv` — map ชื่อ `expw_step` ของ EXAT (เช่น
   "ศรีรัช", "ฉลองรัช", "เฉลิมมหานคร" ฯลฯ ดูรายชื่อที่เจอจริงได้จาก `docs/api_samples/`) ไปยัง
   พิกัดตัวแทนของทางด่วนสายนั้น (หาจาก Google Maps เอง คลิกจุดกึ่งกลางเส้นทางโดยประมาณ)
   บันทึกไว้ใน `docs/` ด้วยว่าใช้เกณฑ์อะไรเลือกจุด เพื่อให้ตรวจสอบย้อนหลังได้
5. เขียน model แยกตาม schema ต้นทาง:
   - `stg_arms_json.sql` — แตก JSONB ของ `raw_arms` เฉพาะแถวที่ `source_format = 'json'`,
     cast type field ตัวพิมพ์ใหญ่ (`LATITUDE`, `DEATH`, ...) ตามที่บันทึกไว้ใน `docs/api_notes.md`
   - `stg_arms_csv.sql` — แตก JSONB เฉพาะแถวที่ `source_format = 'csv'`, cast type field ตัวพิมพ์เล็ก
     (`latitude`, `dead_total`, ...) และ parse วันที่ format `D/M/YYYY` ให้เป็น date จริง
   - `stg_exat.sql` — แตก JSONB ของ `raw_exat`, join กับ seed `expw_step_coordinates` เพื่อเติม
     lat/lng ให้แต่ละแถวจาก `expw_step`
6. เขียน model `stg_accidents.sql` (union ทั้ง 3): map field name ให้ตรงกัน — โดยเฉพาะ column
   ความรุนแรงที่ความละเอียดไม่เท่ากัน (ARMS-CSV แยกชาย/หญิง/เด็ก, ARMS-JSON มีแค่ตัวเลขรวม,
   EXAT แยกแค่ชาย/หญิงไม่มีเด็ก) ให้ normalize เหลือแค่ `dead_total`, `injured_severe_total`,
   `injured_light_total` ที่ทุก schema มีร่วมกัน, เพิ่ม column `source` (`arms_json`/`arms_csv`/`exat`)
   และ `is_geocoded` (true สำหรับ EXAT เพื่อสื่อสารว่าพิกัดนี้เป็นค่าประมาณ ไม่ใช่จุดเกิดเหตุจริง)
7. กรองพิกัดผิดปกตินอกขอบเขตประเทศไทย (lat ~5.6-20.5, lng ~97.3-105.6) ใน model นี้
8. `dbt run` แล้ว query ตรวจผลลัพธ์ใน Postgres
9. เขียน `dbt docs` description สั้นๆ ให้แต่ละ model/column สำคัญ

**Definition of Done:** `dbt run` ผ่าน, มี `stg_accidents` ที่รวมทั้ง 3 schema ต้นทางเป็นแบบเดียวกัน
ข้อมูลพิกัดอยู่ในขอบเขตไทยเท่านั้น (รวมถึงพิกัด geocode ของ EXAT ด้วย)

---

## Issue 08 — dbt clustering layer (DBSCAN)

**เป้าหมาย:** หากลุ่มอุบัติเหตุที่เกิดใกล้กันและซ้ำหลายครั้ง ได้ `cluster_id` ต่อจุด

**ขั้นตอน:**
1. ตัดสินใจวิธี implement DBSCAN — ตัวเลือกหลัก 2 แบบ:
   - PostGIS extension + `ST_ClusterDBSCAN` (ทำใน SQL ล้วน อยู่ใน dbt model ได้)
   - Python-based (scikit-learn `DBSCAN`) รันเป็น script แยก แล้วเขียนผลกลับเข้า Postgres เป็นตารางให้ dbt source ต่อ
   - แนะนำ PostGIS ถ้าต้องการให้ทุกอย่างอยู่ใน dbt/SQL layer ล้วนๆ (สอดคล้องกับสถาปัตยกรรมที่ออกแบบไว้)
2. ถ้าเลือก PostGIS: เปิด extension ใน Postgres (`CREATE EXTENSION postgis`), เพิ่มใน docker image/init script
3. เขียน model `int_accident_clusters.sql`: แปลง lat/lng เป็น geometry point, รัน `ST_ClusterDBSCAN(eps, minpoints)` (eps ตั้งเทียบเป็นองศาหรือแปลงหน่วยเป็นเมตรด้วย `ST_Transform` ไป SRID ที่เหมาะกับไทย เช่น UTM 47N/48N) กำหนดรัศมี 200-500 เมตรตามที่ระบุไว้
4. ทดสอบด้วยข้อมูลจริง เช็คว่า cluster ที่ได้สมเหตุสมผล (plot คร่าวๆ ด้วย Python/QGIS ดูตำแหน่ง)
5. ปรับ `eps`/`minpoints` จนได้ผลลัพธ์ที่ดูสมเหตุสมผล (ไม่ cluster ใหญ่เกินไปจนไม่มีความหมาย หรือเล็กเกินไปจนไม่มี cluster ไหนเกิน 1 จุด)
6. ⚠️ **พิจารณาแยก parameter ตาม `source`:** เพราะพิกัดฝั่ง `exat` เป็นพิกัด geocode ประมาณเอา (จาก
   Issue 07) ความละเอียดหยาบกว่าพิกัดจริงของ `arms_json`/`arms_csv` มาก ถ้าใช้ `eps` เดียวกันหมด
   จุดอุบัติเหตุ EXAT หลายจุดจะถูกจับรวมเป็น cluster เดียวทั้งที่ไม่เกี่ยวข้องกันจริง (เพราะอ้างอิง
   จากพิกัดทางด่วนสายเดียวกัน) — อาจต้อง cluster แยก query ตาม source แล้ว union ผลลัพธ์ทีหลัง
   หรือยอมรับว่า cluster ฝั่ง EXAT สื่อความหมายระดับ "ทางด่วนสายไหน" ไม่ใช่ "จุดไหน"
7. บันทึกเหตุผลการเลือกค่า parameter ไว้ใน comment ของ model หรือ `docs/`

**Definition of Done:** มี model ที่ output `cluster_id` ต่อแถว, ทดสอบแล้วผลลัพธ์สมเหตุสมผลเมื่อเทียบกับแผนที่จริง, มีคำอธิบายชัดเจนว่า cluster ฝั่ง EXAT มีข้อจำกัดเรื่องความละเอียดต่างจาก ARMS

---

## Issue 09 — dbt mart layer (severity score)

**เป้าหมาย:** สร้าง `mart_blackspot_severity` — ตารางพร้อมใช้งานสำหรับแสดงผล

**ขั้นตอน:**
1. ออกแบบสูตร severity score: weighted sum ตามความรุนแรง (เสียชีวิต > บาดเจ็บสาหัส > บาดเจ็บเล็กน้อย > ทรัพย์สินเสียหาย) บวกน้ำหนักตามความถี่ (จำนวนครั้งที่เกิดใน cluster) — เขียนสูตรและเหตุผลไว้เป็น comment ใน model
2. เขียน model `mart_blackspot_severity.sql`: `GROUP BY cluster_id` จาก `int_accident_clusters`, คำนวณ:
   - จำนวนอุบัติเหตุในกลุ่ม
   - centroid (lat/lng เฉลี่ยหรือ `ST_Centroid`) สำหรับปักหมุดบนแผนที่
   - severity score ตามสูตรที่ออกแบบ (ใช้ column ที่ normalize แล้วจาก Issue 07 คือ `dead_total`,
     `injured_severe_total`, `injured_light_total` เพราะแต่ละ source นับความรุนแรงละเอียดไม่เท่ากัน)
   - ช่วงวันที่ min/max ที่มีข้อมูล
   - breakdown ตาม source (`arms_json`/`arms_csv`/`exat`), รวม column `is_geocoded` เพื่อให้ตอน
     publish (Issue 11) แสดงผลต่างกันได้ระหว่างจุดที่มีพิกัดจริงกับจุดที่ประมาณเอา
3. เรียง rank ตาม severity score, เผื่อ column `rank` ไว้ใช้ตอนแสดงผล top-N blackspot
4. `dbt run`, ตรวจผลลัพธ์ query ดูว่า top blackspot ที่ได้สมเหตุสมผล
5. เขียน `dbt docs` description ให้ mart model นี้ครบ (จะใช้ตอน generate docs)

**Definition of Done:** มี `mart_blackspot_severity` พร้อม column ที่พอสำหรับ generate แผนที่และ query top blackspot ได้ทันที

---

## Issue 10 — dbt tests (data quality gate)

**เป้าหมาย:** มี test คุมคุณภาพทุก layer, ถ้า fail ต้องบล็อกไม่ให้ pipeline ไปต่อ

**ขั้นตอน:**
1. เพิ่ม schema tests (`.yml`) ในแต่ละ model:
   - `stg_accidents`: `not_null` บน field สำคัญ (lat, lng, accident_date, source), `unique` บน primary key, custom test เช็คพิกัดอยู่ในขอบเขตไทย (เขียนเป็น singular test ใน `dbt/tests/`)
   - `int_accident_clusters`: `not_null` บน `cluster_id` ที่ควรมีค่า, เช็คไม่มี record ซ้ำ (unique combination ของ key)
   - `mart_blackspot_severity`: `not_null` บน severity score, เช็ค score ไม่ติดลบ, เช็ค count > 0
2. เขียน custom singular test เช่น `tests/assert_coordinates_within_thailand.sql`
3. `dbt test` รันแล้วดู pass/fail ทั้งหมด
4. จงใจทำให้ข้อมูล fail (เช่น inject ข้อมูลพิกัดผิด) ทดสอบว่า test จับได้จริง แล้วเอาข้อมูลทดสอบออก
5. ใน Airflow DAG (จะผูกจริงใน issue 12) วางแผนว่า `dbt test` ต้องรันเป็น task แยกก่อน publish task และถ้า fail DAG ต้องหยุด ไม่ปล่อยต่อ (`on_failure` behavior ปกติของ Airflow อยู่แล้วถ้า task fail แล้ว downstream ไม่รัน)

**Definition of Done:** `dbt test` ครอบคลุมทุก layer หลัก, พิสูจน์แล้วว่าจับข้อมูลเสียได้จริง

---

## Issue 11 — Folium map + publish ขึ้น GitHub Pages

**เป้าหมาย:** Generate แผนที่ HTML จาก mart table และ publish ขึ้น GitHub Pages ได้ (ทำ manual ให้ผ่านก่อน ค่อยผูกเข้า Airflow ใน issue 12)

**ขั้นตอน:**
1. สร้าง branch `gh-pages` หรือใช้โฟลเดอร์ `docs/` บน `main` เป็น source ของ GitHub Pages (ตั้งค่าใน repo Settings → Pages)
2. เขียน `scripts/generate_map.py`: query `mart_blackspot_severity` จาก Postgres → สร้าง Folium map:
   - Heatmap layer จากตำแหน่ง blackspot ถ่วงน้ำหนักด้วย severity score
   - Marker layer คลิกดู popup รายละเอียด (จำนวนครั้ง, severity score, ช่วงวันที่, source)
   - ⚠️ ใช้ column `is_geocoded` (จาก Issue 07/09) แยกสไตล์ marker ระหว่างจุดพิกัดจริง (ARMS) กับ
     จุดพิกัด geocode ประมาณเอา (EXAT) เช่น สีต่างกันหรือใส่คำเตือนใน popup — กันคนดูเข้าใจผิดว่า
     ทุกจุดแม่นยำเท่ากัน
   - Layer control ให้สลับ heatmap/marker ได้
3. Export เป็น `docs/index.html` (หรือ path ที่ตรงกับ GitHub Pages source)
4. รัน script ด้วยข้อมูลจริง เปิดไฟล์ HTML ในเบราว์เซอร์ตรวจสอบว่าแสดงผลถูกต้อง ใช้งานได้ (zoom, click popup)
5. Commit + push ไฟล์ HTML ขึ้น branch ที่ตั้งเป็น Pages source, รอ GitHub Pages build, เปิดลิงก์สาธารณะตรวจสอบว่าเข้าถึงได้จริงโดยไม่ login
6. เขียน `scripts/publish_map.py` หรือ shell script ที่ทำ commit+push อัตโนมัติ (จะเอาไปเรียกจาก Airflow ใน issue 12) — ตั้งค่า git credential/deploy key ที่ Airflow container ใช้ push ได้ (เก็บเป็น secret ไม่ commit ลง repo)

**Definition of Done:** มีลิงก์ GitHub Pages ที่เปิดดูแผนที่ได้จริงจากที่ไหนก็ได้โดยไม่ต้อง login, มี script generate+publish ที่รันซ้ำได้

---

## Issue 12 — ผูก dbt run + publish เข้า Airflow DAG (end-to-end)

**เป้าหมาย:** DAG เดียวรันครบ extract → load → dbt run → dbt test → generate map → publish อัตโนมัติทุกวัน

**ขั้นตอน:**
1. ขยาย DAG จาก issue 06 (หรือสร้าง DAG ใหม่ที่ include task เดิมเป็น TaskGroup) เพิ่ม task:
   - `dbt_run` (เรียกผ่าน `BashOperator` หรือ `dbt-core` python API หรือ Cosmos/dbt Airflow provider ถ้าอยากได้ task ต่อ model)
   - `dbt_test` (ต้องรันหลัง `dbt_run` และต้อง fail DAG ถ้า test ไม่ผ่าน)
   - `generate_map` (เรียก `scripts/generate_map.py`)
   - `publish_map` (เรียก `scripts/publish_map.py`)
2. ตั้ง dependency ให้ถูกลำดับ: `[extract_arms, extract_exat] >> [load_arms, load_exat] >> dbt_run >> dbt_test >> generate_map >> publish_map`
3. ตั้งให้ `generate_map`/`publish_map` มี `trigger_rule` ปกติ (รันเฉพาะเมื่อ upstream สำเร็จทั้งหมด) เพื่อให้ data ที่ fail test ไม่หลุดไป publish
4. เพิ่ม Airflow Variables/Connections ที่ต้องใช้ (git credential, dbt profile path) ผ่าน UI หรือ `.env`
5. Trigger DAG เต็มรูปแบบ manual ทดสอบ end-to-end อย่างน้อย 1 รอบสำเร็จ
6. ทดสอบ failure path: จงใจทำ dbt test fail แล้วยืนยันว่า `generate_map`/`publish_map` ไม่ถูกรัน
7. เปิด schedule `@daily` จริง ปล่อยรันอัตโนมัติสัก 2-3 วันดูผล

**Definition of Done:** DAG เดียวรันครบวงจรอัตโนมัติ, พิสูจน์แล้วว่าข้อมูลเสียไม่หลุดไปถึงแผนที่สาธารณะ

---

## Issue 13 — README + เอกสารโครงงาน + finalize

**เป้าหมาย:** โปรเจกต์พร้อมใส่ resume/พอร์ต และคนอื่น clone ไปรันตามได้

**ขั้นตอน:**
1. เขียน README.md ฉบับเต็ม: ปัญหาที่แก้, สถาปัตยกรรม (แนบ diagram), tech stack, วิธี setup local, ลิงก์แผนที่ live demo, screenshot
2. เพิ่ม architecture diagram (draw.io/excalidraw export เป็นภาพ หรือ mermaid ใน README)
3. รวบรวม `docs/` ให้เป็นระเบียบ (api_notes, local_setup, decision log ของ DBSCAN parameter ฯลฯ)
4. เขียน bullet point สำหรับ resume ในนี้ตามที่ร่างไว้ ปรับให้ตรงกับผลจริงที่ทำได้ (ตัวเลขจริง เช่น "clustered N accidents into M blackspots")
5. เช็ค `.env.example` ครบถ้วน, ไม่มี secret หลุดใน git history (`git log -p | grep` เช็คคร่าวๆ)
6. Tag release แรก (เช่น `v1.0.0`) บน GitHub

**Definition of Done:** README ที่คนแปลกหน้าอ่านแล้วเข้าใจและ clone ไปรันได้, ลิงก์แผนที่ demo ใช้งานได้จริง

---

## Issue 14 (Optional) — REST API เผยแพร่ blackspot data

**เป้าหมาย:** endpoint ให้ระบบอื่นดึง blackspot data ไปใช้ต่อ (เช่น FastAPI)

**ขั้นตอน:**
1. เลือก framework (แนะนำ FastAPI — เบาและมี auto docs)
2. สร้าง endpoint `GET /blackspots` (list พร้อม filter ตาม severity/พื้นที่), `GET /blackspots/{id}`
3. เชื่อมต่อ Postgres อ่านจาก `mart_blackspot_severity` (read-only user แยกจาก pipeline user)
4. เพิ่ม pagination, basic rate limiting
5. เขียน Dockerfile แยกสำหรับ service นี้ เพิ่มเข้า docker-compose
6. Deploy (เลือก platform ฟรี เช่น Render/Fly.io) หรือรันคู่กับ infra เดิม
7. เขียน API docs (FastAPI auto-gen ที่ `/docs`) และอัปเดต README

**Definition of Done:** เรียก endpoint จริงได้จาก internet, มี docs

---

## Issue 15 (Optional) — LINE Bot แจ้งเตือนจุดเสี่ยง

**เป้าหมาย:** ผู้ใช้ระบุเส้นทาง แล้วบอทแจ้งจุดเสี่ยงตามเส้นทางนั้น

**ขั้นตอน:**
1. สมัคร LINE Messaging API channel, ได้ channel secret/access token
2. ออกแบบ flow ง่ายๆ: user ส่งจุดเริ่มต้น-ปลายทาง (หรือ share location) → bot query blackspot ที่อยู่ใกล้เส้นทาง (ใช้ REST API จาก issue 14 หรือ query ตรง)
3. เขียน webhook handler (FastAPI/Flask) รับ event จาก LINE, ตอบกลับด้วย Flex Message แสดงจุดเสี่ยงและ severity
4. Deploy webhook ให้มี public HTTPS URL (ngrok สำหรับ dev, จริงจังใช้ platform เดียวกับ issue 14)
5. ทดสอบผ่าน LINE app จริง
6. อัปเดต README เพิ่มวิธีใช้บอท

**Definition of Done:** เพิ่มบอทเป็นเพื่อนใน LINE แล้วใช้งานได้จริงตาม flow ที่ออกแบบ
