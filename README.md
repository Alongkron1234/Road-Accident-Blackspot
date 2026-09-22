# Road Accident Blackspot Pipeline

โปรเจกต์ ELT pipeline อัตโนมัติที่ดึงข้อมูลอุบัติเหตุถนนจาก Open Data ของหน่วยงานราชการไทย
มารวม, clean, จัดกลุ่มจุดที่เกิดอุบัติเหตุซ้ำๆ ("blackspot") แล้วเผยแพร่เป็นแผนที่
interactive สาธารณะ — ใครก็เข้าดูได้ ไม่ต้อง login

> **สถานะ:** กำลังพัฒนา ดูแผนงานแบบละเอียดเป็นราย Issue ได้ที่ [PLAN.md](PLAN.md)

---

## ปัญหาที่แก้

ข้อมูลอุบัติเหตุถนนของไทยกระจายอยู่หลายหน่วยงาน แต่ละที่เผยแพร่คนละ format ไม่มีใคร
เอามารวมแล้ววิเคราะห์อย่างเป็นระบบว่า *จุดไหนเกิดอุบัติเหตุซ้ำๆ* ทั้งที่เป็นข้อมูลที่มี
ประโยชน์จริงต่อทั้งคนขับรถและหน่วยงานวางแผนความปลอดภัยถนน

## โปรเจกต์นี้ทำอะไรบ้าง

1. ดึงข้อมูลอุบัติเหตุทุกวันจาก Open Data API ของหน่วยงานราชการ 2 แห่ง
2. โหลดข้อมูลดิบเข้า PostgreSQL ก่อน โดยยังไม่แปลงอะไร (ดูเหตุผลที่หัวข้อ [ทำไมถึงใช้ ELT](#ทำไมถึงใช้-elt))
3. แปลงข้อมูลในตัว database เองด้วย dbt: รวม schema ให้เป็นแบบเดียวกัน → จัดกลุ่มจุดที่
   เกิดอุบัติเหตุซ้ำใกล้กัน (DBSCAN) → คำนวณ severity score ต่อกลุ่ม
4. คุมคุณภาพข้อมูลด้วย dbt tests ก่อนปล่อยไปถึง output
5. Generate แผนที่ Folium แบบ live แล้ว publish ขึ้น GitHub Pages อัตโนมัติ

**แผนที่ live:** _(จะใส่ลิงก์เมื่อทำ Issue 11 เสร็จ)_

---

## แหล่งข้อมูล

| Source | หน่วยงาน | ข้อมูล | Format |
|---|---|---|---|
| `arms_accident` API | กรมทางหลวงชนบท | อุบัติเหตุบนทางหลวงชนบท, real-time | JSON |
| `exat-accident` API | การทางพิเศษแห่งประเทศไทย | อุบัติเหตุบนทางด่วน, รายเดือน | JSON |

ทั้งสอง endpoint เผยแพร่ผ่าน [datagov.mot.go.th](https://datagov.mot.go.th)
(Open Data กระทรวงคมนาคม) license "Open Data Common" เข้าถึงได้ไม่จำกัด

---

## สถาปัตยกรรม

```
 ┌──────────────┐        ┌──────────────┐
 │   ARMS API   │        │   EXAT API   │
 │ (ทางหลวงชนบท) │        │   (ทางด่วน)   │
 └──────┬───────┘        └──────┬───────┘
        │                       │
        │      1. Extract       │
        └───────────┬───────────┘
                     ▼
              2. Load (raw)
        raw_arms  /  raw_exat  (JSONB, PostgreSQL)
                     │
                     │  3. Transform (dbt) — staging
                     ▼
              stg_accidents
                     │
                     │  4. Transform (dbt) — clustering (DBSCAN)
                     ▼
           int_accident_clusters
                     │
                     │  5. Transform (dbt) — mart
                     ▼
          mart_blackspot_severity
                     │
                     │  6. dbt test  (คุมคุณภาพ, fail แล้วหยุดทันที)
                     ▼
              7. Publish
           Folium map → GitHub Pages
              (public, static)
```

ทั้ง 7 ขั้นตอนถูกควบคุมด้วย Airflow DAG เดียวที่รันอัตโนมัติทุกวัน

## ทำไมถึงใช้ ELT

JSON ดิบจะถูกโหลดเข้า Postgres ก่อน (`raw_arms`, `raw_exat`) โดยยังไม่แปลงอะไรทั้งสิ้น
logic การแปลงข้อมูลทั้งหมดอยู่ใน dbt ซึ่งทำงานอยู่ *ใน* database เอง ข้อดีคือถ้าวันหนึ่ง
ต้องปรับรัศมี clustering หรือสูตร severity score ก็แค่รัน dbt ใหม่กับข้อมูลดิบที่ยังอยู่ใน
Postgres — ไม่ต้องยิง API ของหน่วยงานราชการใหม่เพื่อ reprocess ข้อมูลย้อนหลัง

---

## Tech Stack

- **Orchestration:** Apache Airflow — DAG รันทุกวันดูแลทั้ง pipeline
- **Storage:** PostgreSQL (+ PostGIS) — เก็บทั้ง raw layer และ transformed layer
- **Transform:** dbt — SQL-based transformation พร้อม data tests
- **Geospatial clustering:** PostGIS `ST_ClusterDBSCAN` — จัดกลุ่มอุบัติเหตุที่เกิดซ้ำ
  ในรัศมี ~200-500 เมตร
- **Visualization:** Folium (Python, wrap Leaflet.js)
- **Hosting:** GitHub Pages — เผยแพร่แบบ static, ฟรี, ไม่ต้องดูแล server
- **Language:** Python (extract, orchestration) + SQL (dbt models)

---

## ขั้นตอนของ Pipeline

1. **Extract** — Airflow DAG ยิง request ไปทั้ง 2 API พร้อมกันทุกวัน พร้อม retry logic
   เผื่อ API รัฐไม่เสถียร เก็บ response เป็น JSON ดิบตามที่ได้มา
2. **Load (raw layer)** — โยน JSON ดิบเข้า `raw_arms` / `raw_exat` เป็น JSONB ตรงๆ
   ยังไม่แปลงข้อมูล ยังไม่รวม schema
3. **Transform (dbt)**
   - *Staging* — แปลง JSON เป็น column ปกติ, กรองพิกัดที่อยู่นอกขอบเขตประเทศไทยออก,
     map ทั้งสอง source ให้เป็น schema เดียวกันคือ `stg_accidents`
   - *Clustering* — `ST_ClusterDBSCAN` จัดกลุ่มอุบัติเหตุที่เกิดซ้ำใกล้กันให้ได้ `cluster_id`
   - *Mart* — aggregate ต่อ cluster คำนวณ severity score (ถ่วงน้ำหนักตามความรุนแรง +
     ความถี่) → ได้ตาราง `mart_blackspot_severity`
4. **Test (dbt tests)** — พิกัดต้องอยู่ในขอบเขตไทย, field สำคัญห้าม null, ห้ามมี record
   ซ้ำ ถ้า test fail DAG จะไม่ปล่อยข้อมูลไปต่อจนถึงขั้น publish
5. **Publish** — query จากตาราง mart → generate แผนที่ HTML ด้วย Folium →
   commit/push ขึ้น GitHub Pages อัตโนมัติ เป็น task สุดท้ายของ DAG

---

## วิธี setup ใช้งาน local

ขั้นตอน setup แบบละเอียดจะอยู่ที่ [`docs/local_setup.md`](docs/local_setup.md)
หลังจากทำ Issue 03 (Docker Compose infra) เสร็จ คร่าวๆ จะเป็นแบบนี้:

```bash
git clone <repo-url>
cd Road_Accident\ Blackspot_Pipeline
cp .env.example .env   # ใส่ credential ให้ครบ
docker compose up -d
```

- Airflow UI: `localhost:8080`
- Postgres: `localhost:5432`

---

## โครงสร้างโปรเจกต์

```
├── airflow/dags/     # Airflow DAG
├── dbt/              # dbt project (staging, clustering, mart models + tests)
├── extract/          # API extractor + raw-layer loader
├── scripts/          # generate แผนที่, publish ขึ้น GitHub Pages
├── docs/             # API notes, setup docs, decision log
├── docker-compose.yml
└── PLAN.md           # แผนงานแบบละเอียดเป็นราย Issue
```

---

## แผนงานถัดไป

ดูรายละเอียดทั้งหมดแบ่งเป็น Issue/branch ได้ที่ [PLAN.md](PLAN.md) — ตั้งแต่
scaffold repo ไปจนถึงผูก DAG แบบ end-to-end พร้อม feature เสริม (REST API,
LINE bot แจ้งเตือนจุดเสี่ยง)
