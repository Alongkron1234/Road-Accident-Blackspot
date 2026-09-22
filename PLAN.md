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

## Issue 02 — สำรวจ/ทดสอบ API จริง (ARMS, EXAT)

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

**เป้าหมาย:** ได้ Python script ที่ดึงข้อมูลจากทั้งสอง API แล้วเซฟเป็น JSON ดิบ พร้อม retry logic

**ขั้นตอน:**
1. สร้าง `extract/arms_extractor.py` และ `extract/exat_extractor.py` (หรือใช้ base class ร่วมถ้าโครงสร้างคล้ายกันมากพอ — อย่า over-abstract ถ้าไม่จำเป็น)
2. ใช้ `requests` + retry (เช่น `tenacity` หรือ manual retry with backoff) รองรับกรณี API รัฐ timeout/500
3. Handle pagination ตามที่บันทึกไว้ใน issue 02 จนกว่าจะดึงข้อมูลครบ
4. เซฟผลลัพธ์เป็นไฟล์ JSON ดิบ พร้อม timestamp ในชื่อไฟล์ เช่น `data/raw/arms_20260101.json` (โฟลเดอร์นี้อยู่ใน `.gitignore` ไม่ commit ข้อมูลจริง)
5. เขียน unit test เบื้องต้น (mock HTTP response) เช็ค parsing/retry logic ทำงานถูกต้อง — ใช้ `pytest` + `responses`/`unittest.mock`
6. รัน script จริงกับ API จริงหนึ่งรอบ ยืนยันว่าได้ข้อมูลจริงและไฟล์ JSON ถูกต้อง

**Definition of Done:** รัน `python extract/arms_extractor.py` และ `exat_extractor.py` แล้วได้ไฟล์ JSON ดิบจริง, มี test ผ่าน, มี retry ที่ทดสอบแล้วว่าทำงาน

---

## Issue 05 — Load raw layer เข้า Postgres

**เป้าหมาย:** โหลด JSON ดิบเข้า Postgres เป็น `raw_arms`, `raw_exat` โดยไม่แปลงข้อมูล (ตาม ELT)

**ขั้นตอน:**
1. ออกแบบ schema ตาราง raw: เก็บเป็น `JSONB` column (เช่น `payload jsonb`, `source_file text`, `loaded_at timestamptz`, `id serial`) — ให้ยืดหยุ่นรองรับ schema เปลี่ยนแปลงจาก API ได้
2. เขียน SQL migration หรือ `CREATE TABLE IF NOT EXISTS` script ใน `dbt/` (เป็น seed/pre-hook) หรือแยกเป็น `scripts/init_db.sql`
3. เขียน `extract/loader.py` อ่านไฟล์ JSON ดิบ → insert เข้า `raw_arms`/`raw_exat` ผ่าน `psycopg2`/`sqlalchemy`
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

**เป้าหมาย:** ตั้ง dbt project เชื่อม Postgres ได้ และมี `stg_accidents` schema เดียวกันจากทั้งสอง source

**ขั้นตอน:**
1. `dbt init` ใน `dbt/`, ตั้งค่า `profiles.yml` ชี้ไป Postgres ใน docker-compose (ใช้ env var ผ่าน `env_var()` ไม่ hardcode credential)
2. `dbt debug` ยืนยัน connection ผ่าน
3. เขียน dbt source definition ชี้ไปตาราง `raw_arms`, `raw_exat`
4. เขียน model `stg_arms.sql`, `stg_exat.sql`: แตก JSONB เป็น column ปกติ (`->>` operator), cast type ให้ถูก (lat/lng เป็น numeric, วันที่เป็น timestamp)
5. เขียน model `stg_accidents.sql` (union ทั้งสอง): map field name ให้ตรงกันตามที่บันทึกไว้ใน `docs/api_notes.md`, เพิ่ม column `source` บอกว่าแถวนี้มาจาก arms หรือ exat
6. กรองพิกัดผิดปกตินอกขอบเขตประเทศไทย (lat ~5.6-20.5, lng ~97.3-105.6) ใน model นี้
7. `dbt run` แล้ว query ตรวจผลลัพธ์ใน Postgres
8. เขียน `dbt docs` description สั้นๆ ให้แต่ละ model/column สำคัญ

**Definition of Done:** `dbt run` ผ่าน, มี `stg_accidents` ที่รวมสอง source เป็น schema เดียวกัน ข้อมูลพิกัดอยู่ในขอบเขตไทยเท่านั้น

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
6. บันทึกเหตุผลการเลือกค่า parameter ไว้ใน comment ของ model หรือ `docs/`

**Definition of Done:** มี model ที่ output `cluster_id` ต่อแถว, ทดสอบแล้วผลลัพธ์สมเหตุสมผลเมื่อเทียบกับแผนที่จริง

---

## Issue 09 — dbt mart layer (severity score)

**เป้าหมาย:** สร้าง `mart_blackspot_severity` — ตารางพร้อมใช้งานสำหรับแสดงผล

**ขั้นตอน:**
1. ออกแบบสูตร severity score: weighted sum ตามความรุนแรง (เสียชีวิต > บาดเจ็บสาหัส > บาดเจ็บเล็กน้อย > ทรัพย์สินเสียหาย) บวกน้ำหนักตามความถี่ (จำนวนครั้งที่เกิดใน cluster) — เขียนสูตรและเหตุผลไว้เป็น comment ใน model
2. เขียน model `mart_blackspot_severity.sql`: `GROUP BY cluster_id` จาก `int_accident_clusters`, คำนวณ:
   - จำนวนอุบัติเหตุในกลุ่ม
   - centroid (lat/lng เฉลี่ยหรือ `ST_Centroid`) สำหรับปักหมุดบนแผนที่
   - severity score ตามสูตรที่ออกแบบ
   - ช่วงวันที่ min/max ที่มีข้อมูล
   - breakdown ตาม source (arms/exat) ถ้ามีประโยชน์
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
