# Road Accident Blackspot Pipeline

โปรเจกต์นี้ดึงข้อมูลอุบัติเหตุบนท้องถนนจาก Open Data ของหน่วยงานราชการไทย เอามารวม
เอามา clean แล้วหาว่าจุดไหนเกิดอุบัติเหตุซ้ำๆ บ่อยๆ (เรียกว่า "blackspot") จากนั้นก็ทำเป็น
แผนที่ interactive ให้ใครก็เข้าดูได้เลยโดยไม่ต้อง login ทั้งกระบวนการรันอัตโนมัติทุกวัน



---

## ทำไมถึงทำโปรเจกต์นี้

ข้อมูลอุบัติเหตุถนนบ้านเรากระจัดกระจายอยู่คนละหน่วยงาน แต่ละที่ก็เผยแพร่คนละ format
ไม่มีใครเอามารวมกันแล้วดูอย่างจริงจังว่า *จุดไหนที่เกิดอุบัติเหตุซ้ำแล้วซ้ำอีก* ทั้งที่
ข้อมูลแบบนี้มีประโยชน์มากทั้งกับคนขับรถทั่วไปและหน่วยงานที่ต้องวางแผนความปลอดภัยถนน

## โดยสรุปโปรเจกต์นี้ทำอะไร

1. ไปดึงข้อมูลอุบัติเหตุจาก API ของหน่วยงานราชการ 2 แห่งทุกวัน
2. เก็บข้อมูลดิบเข้า PostgreSQL ก่อนเลย ยังไม่แตะไม่แปลงอะไรทั้งนั้น (อธิบายเหตุผลไว้ที่
   หัวข้อ [ทำไมถึงใช้ ELT](#ทำไมถึงใช้-elt))
3. ค่อยมาแปลงข้อมูลทีหลังด้วย dbt ตรงๆ ใน database เลย: รวม schema ของสอง source ให้
   เหมือนกัน → จัดกลุ่มจุดที่เกิดอุบัติเหตุซ้ำใกล้ๆ กัน (DBSCAN) → คิด severity score
   ของแต่ละกลุ่ม
4. ก่อนปล่อยข้อมูลออกไปให้ dbt tests เช็คคุณภาพก่อน ถ้ามีอะไรผิดปกติจะไม่ปล่อยผ่าน
5. generate แผนที่ด้วย Folium แล้ว publish ขึ้น GitHub Pages ให้เองอัตโนมัติ


---

## แหล่งข้อมูล

| Source | หน่วยงาน | ข้อมูล | Format |
|---|---|---|---|
| `arms_accident` API | กรมทางหลวงชนบท | อุบัติเหตุบนทางหลวงชนบท, ค่อนข้าง real-time | JSON |
| `exat-accident` API | การทางพิเศษแห่งประเทศไทย | อุบัติเหตุบนทางด่วน, อัปเดตรายเดือน | JSON |

ทั้งคู่เผยแพร่ผ่าน [datagov.mot.go.th](https://datagov.mot.go.th) (Open Data ของ
กระทรวงคมนาคม) license เป็น "Open Data Common" เข้าถึงได้อิสระ ไม่มีข้อจำกัด

---

## หน้าตา pipeline

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
                     │  6. dbt test  (เช็คคุณภาพ ถ้าพังหยุดตรงนี้เลย)
                     ▼
              7. Publish
           Folium map → GitHub Pages
              (public, static)
```

ทุกขั้นตอนตั้งแต่ 1-7 ถูกควบคุมด้วย Airflow DAG เดียว รันให้เองอัตโนมัติทุกวัน

## ทำไมถึงใช้ ELT

ข้อมูลดิบจะถูกโหลดเข้า Postgres ก่อนเสมอ (`raw_arms`, `raw_exat`) แบบไม่ผ่านการแปลงใดๆ
ส่วน logic การแปลงข้อมูลทั้งหมดไปอยู่ใน dbt ที่ทำงานอยู่ในตัว database เลย ข้อดีคือถ้าวัน
ไหนอยากปรับรัศมี clustering หรือแก้สูตร severity score ก็แค่สั่งรัน dbt ใหม่กับข้อมูลดิบที่
ยังอยู่ใน Postgres ครบทุกก้อน ไม่ต้องไปยิง API ของหน่วยงานราชการซ้ำเพื่อดึงข้อมูล
ย้อนหลังมาใหม่

---

## Tech Stack

- **Orchestration:** Apache Airflow — คุม DAG ที่รันทุกวัน
- **Storage:** PostgreSQL (+ PostGIS) — เก็บทั้ง raw layer และ transformed layer
- **Transform:** dbt — เขียน transformation เป็น SQL พร้อม data tests ในตัว
- **Geospatial clustering:** PostGIS `ST_ClusterDBSCAN` — จัดกลุ่มอุบัติเหตุที่เกิดซ้ำ
  ในรัศมีประมาณ 200-500 เมตร
- **Visualization:** Folium (Python, ห่อ Leaflet.js อีกที)
- **Hosting:** GitHub Pages — เผยแพร่เป็น static site ฟรี ไม่ต้องดูแล server เอง
- **Language:** Python (ฝั่ง extract/orchestration) + SQL (ฝั่ง dbt models)

---

## รายละเอียดแต่ละขั้นตอน

1. **Extract** — Airflow DAG ยิง request ไปทั้ง 2 API พร้อมกันทุกวัน มี retry logic
   เผื่อ API หน่วยงานรัฐหลุดหรือล่มบ่อยๆ ได้ response มาก็เก็บเป็น JSON ดิบตามที่ได้
2. **Load (raw layer)** — เอา JSON ดิบยัดเข้า `raw_arms` / `raw_exat` ตรงๆ เก็บเป็น
   JSONB ยังไม่แปลง ยังไม่รวม schema อะไรทั้งนั้น
3. **Transform (dbt)**
   - *Staging* — แกะ JSON ออกมาเป็น column ปกติ, กรองพิกัดที่หลุดออกนอกขอบเขต
     ประเทศไทยทิ้ง, แล้ว map ทั้งสอง source ให้อยู่ใน schema เดียวกันคือ `stg_accidents`
   - *Clustering* — ใช้ `ST_ClusterDBSCAN` จับกลุ่มอุบัติเหตุที่เกิดซ้ำอยู่ใกล้กัน ได้
     `cluster_id` ออกมา
   - *Mart* — aggregate ข้อมูลตาม cluster แล้วคำนวณ severity score (ถ่วงน้ำหนักตาม
     ความรุนแรง + ความถี่ที่เกิด) ได้ตาราง `mart_blackspot_severity`
4. **Test (dbt tests)** — เช็คว่าพิกัดต้องอยู่ในขอบเขตไทยจริง, field สำคัญห้าม null,
   ห้ามมี record ซ้ำ ถ้า test ไหน fail DAG จะหยุดตรงนั้นเลย ไม่ปล่อยให้ไปถึงขั้น publish
5. **Publish** — query ข้อมูลจากตาราง mart มา generate เป็นแผนที่ HTML ด้วย Folium
   แล้ว commit/push ขึ้น GitHub Pages ให้เองอัตโนมัติ เป็น task สุดท้ายของ DAG

---

## อยาก setup รันเองที่เครื่อง

```bash
git clone <repo-url>
cd Road_Accident\ Blackspot_Pipeline
cp .env.example .env   # ใส่ credential ให้ครบก่อน
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

## อยากรู้ว่าต่อไปจะทำอะไร

ดูรายละเอียดทั้งหมดที่แบ่งเป็น Issue/branch ได้ที่ [PLAN.md](PLAN.md) — ไล่ตั้งแต่
scaffold repo ไปจนถึงผูก DAG ให้รันครบวงจร บวกฟีเจอร์เสริมท้ายๆ อย่าง REST API
กับ LINE bot แจ้งเตือนจุดเสี่ยง
