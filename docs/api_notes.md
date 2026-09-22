# API Notes — ARMS & EXAT

บันทึกจากการสำรวจ API จริง (Issue 02) ทดสอบด้วย `curl` วันที่ 2026-09-22
Sample response เก็บไว้ที่ [`api_samples/`](api_samples/)

---

## 1. ARMS (`arms_accident`) — กรมทางหลวงชนบท

**⚠️ ไม่ใช่ REST API — เป็นไฟล์ให้โหลดตรงๆ (static export) แต่มีถึง 4 resource แยกกัน**

Dataset นี้บน datagov ไม่ได้มีแค่ไฟล์เดียว มี 4 resource:

| Resource | Format | ปีงบประมาณ | จำนวน record | lat/lng null |
|---|---|---|---|---|
| `accident.json` | JSON | ~2565 (CY2022) | 209 | 0 |
| `2566_accident_drr.csv` | CSV | 2566 (ต.ค.65–ก.ย.66) | 1,090 | 0 |
| `2567_accident_drr.csv` | CSV | 2567 (ต.ค.66–ก.ย.67) | 970 | 0 |
| `2568_accident_drr.csv` | CSV | 2568 (ต.ค.67–ปัจจุบัน ปีงบยังไม่จบ) | 814 | 0 |

**รวม ~3,083 record ทั้งหมดมีพิกัดครบ ไม่มี null เลย** — เพียงพอสำหรับทำ clustering จริงจัง
ไม่ได้มีแค่ 209 record แบบที่กลัวไว้ตอนแรก (ตอน Issue 04 ต้องดึงมาให้ครบทั้ง 4 resource)

- **Method:** `GET` ธรรมดา ไม่ต้อง auth / API key ทุก resource
- **Pagination:** ไม่มี — แต่ละไฟล์โหลดมาทั้งก้อนทีเดียว
- ยังไม่พบ endpoint แบบ REST ที่ query ปีอื่นแบบไดนามิกได้ (เช็คหน้า `arms.drr.go.th` แล้ว พบว่าเป็นระบบเว็บสำหรับ staff login เท่านั้น ไม่มี public API/open data section — ข้อมูลเปิดทั้งหมดมาจาก dataportal.drr.go.th 4 resource นี้เท่านั้น)
- คำว่า "real-time" ในหน้า catalog น่าจะหมายถึงระบบหลังบ้านของหน่วยงาน ไม่ใช่ตัว open data export ที่เราใช้ได้ — export นี้อัปเดตปีละครั้ง/ตามรอบปีงบประมาณ

### ⚠️ Schema ของ JSON กับ CSV ไม่เหมือนกัน ต้อง handle แยก

**JSON** (`accident.json`) — field ตัวพิมพ์ใหญ่แบบ SQL export, โครงสร้าง response คือ
`{"<SQL query ดิบ>": [ {record...}, ... ]}` (key บนสุดคือ query string ต้อง `list(d.keys())[0]`)

| Field | ตัวอย่างค่า | หมายเหตุ |
|---|---|---|
| `ID`, `ACCIDENT_ID` | `4854`, `22768` | primary key |
| `ACCIDENT_DATETIME` | `"2021-12-31T17:00:00.000Z"` | ISO datetime พร้อม timezone |
| `LATITUDE`, `LONGITUDE` | `8.164722`, `98.939351` | |
| `PROVINCE_NAME`, `DEPARTMENT_NAME` | `"กระบี่"` | ชื่อจังหวัด |
| `ROAD_NAME_CRD` | `"บ้านกระบี่ใหญ่ - บ้านโพธิ์เรียง"` | ชื่อถนน |
| `KM` | `"6+900"` | string format กม+เมตร ต้อง parse เอง |
| `DEATH`, `WOUNDEDSEVERE`, `WOUNDEDLIGHT` | `0`, `1`, `0` | จำนวนคนตาย/บาดเจ็บสาหัส/บาดเจ็บเล็กน้อย |
| `SUMMARY` | ข้อความบรรยายเหตุการณ์ | free text ยาว |
| `YEAR` | `"2022"` | เป็น **string** |

**CSV** (`2566/2567/2568_accident_drr.csv`) — field ตัวพิมพ์เล็ก cleaner กว่า JSON มาก:

```
id, road_no, road_name, km, accident_date, accident_time, type_accident,
weather_accident, dead_men, dead_women, dead_child_men, dead_child_women, dead_total,
injury_severe_men, injury_severe_women, injury_severe_child_men, injury_severe_child_women,
injury_severe_total, injury_less_men, injury_less_women, injury_less_child_men,
injury_less_child_women, injury_less_total, accident_vehicle, crash_pattern, cause,
longitude, latitude
```

จุดต่างสำคัญจาก JSON:
- `accident_date` เป็น format **`D/M/YYYY`** (เช่น `2/10/2022`) ไม่ใช่ ISO เหมือน JSON — ต้อง parse คนละแบบ
- แยกจำนวนตาย/บาดเจ็บเป็น ชาย/หญิง/เด็กชาย/เด็กหญิง/รวม ละเอียดกว่า JSON (ที่มีแค่ตัวเลขรวม)
- ไม่มี `SUMMARY` (คำบรรยายเหตุการณ์แบบ free text) แต่มี `crash_pattern`, `accident_vehicle` แยก column
- column พิกัดชื่อ `longitude, latitude` (ตัวพิมพ์เล็ก, สลับลำดับกับ JSON ที่เป็น `LATITUDE, LONGITUDE`)

---

## 2. EXAT (`exat-accident`) — การทางพิเศษแห่งประเทศไทย

**✅ REST API จริง**

- **Base URL:** `https://exat-man.web.app/api/EXAT_Accident/{ปี พ.ศ.}/{เดือน}`
- **ตัวอย่างที่ทดสอบแล้วใช้ได้จริง:** `https://exat-man.web.app/api/EXAT_Accident/2564/1`
- **Docs:** `https://exat-man.web.app/docs` เป็น Swagger UI, ดึง spec ดิบจริงได้ที่ `https://exat-man.web.app/openapi.json` (เก็บไว้ที่ `api_samples/exat_openapi.json`)
- **Method:** `GET`, ไม่ต้อง auth / API key
- **Pagination:** ⚠️ **path segment ที่สองไม่ใช่ page number แต่คือ "เดือน" (1-12)** — ยืนยันแล้วโดยเทียบจำนวน record ต่อเดือนกับตัวเลขใน `EXAT_AccidentStat` ตรงกันเป๊ะ (เดือน 1 = 41 record, เดือน 3 = 85 record)
- **ปีเป็นพุทธศักราช (พ.ศ.)** เช่น `2564` = ค.ศ. 2021

### Endpoint อื่นๆ ของ EXAT ที่เจอเพิ่ม (จาก openapi.json)

ระบบนี้มี endpoint มากกว่าที่ catalog ระบุไว้ตั้งเยอะ:

| Endpoint | คืออะไร | มีพิกัดไหม |
|---|---|---|
| `/api/EXAT_Accident/{year}/{month}` | อุบัติเหตุรายครั้ง (ตัวหลักที่จะใช้) | ❌ |
| `/api/EXAT_Crash/{year}/{month}` | เหตุขัดข้อง/รถเสียบนทางด่วน (คนละประเภทกับอุบัติเหตุ ไม่อยู่ใน scope โปรเจกต์นี้) | ❌ |
| `/api/EXAT_AccidentStat/{year}` | สถิติอุบัติเหตุรายเดือน (ใช้ validate เท่านั้น ตามที่สรุปไว้หัวข้อ 3) | ❌ (เป็น aggregate) |
| `/api/EXAT_CrashStat/{year}` | สถิติเหตุขัดข้องรายเดือน | ❌ |
| `/api/EXAT_Plaza` | รายชื่อด่านเก็บเงินทุกด่าน มีแค่ `highway_name` + `plaza_name` | ❌ ไม่มีพิกัดด่านด้วยซ้ำ |
| `/api/EXAT_TrafficStatByPlaza/{year}` | สถิติปริมาณจราจรผ่านด่าน | ❌ ไม่เกี่ยวกับอุบัติเหตุ |
| `/api/EXAT_TrafficStatByCar/{year}` | สถิติปริมาณจราจรตามประเภทรถ | ❌ ไม่เกี่ยวกับอุบัติเหตุ |

**สรุป: เช็คครบทุก endpoint ของ EXAT แล้ว ไม่มีตัวไหนให้พิกัดมาเลยสักตัว แม้แต่รายชื่อด่านเก็บเงิน
ก็ไม่มีพิกัด** ยืนยันว่าการตัดสินใจ geocode เองด้วย lookup table เป็นทางเดียวที่ทำได้จริง

### Response structure
```json
{ "resultCode": 0, "result": [ {record...}, ... ] }
```

### Field ทั้งหมดที่มี (มีแค่ 10 field เท่านั้น)

| Field | ตัวอย่างค่า | หมายเหตุ |
|---|---|---|
| `_id` | `1` | ลำดับในเดือนนั้นๆ ไม่ใช่ unique ID ข้ามเดือน/ปี ต้องประกอบ key เอง (เช่น `year_month_id`) |
| `accident_date` | `"2021-01-30"` | ISO date (ค.ศ. ตรงนี้กลับเป็นปีสากล ไม่ใช่ พ.ศ. แบบใน URL — งงแต่เป็นแบบนี้จริง) |
| `accident_time` | `"12:56"` | |
| `expw_step` | `"ศรีรัช"` | **ชื่อทางด่วนเป็น text เท่านั้น ไม่มีพิกัด** ดูหัวข้อถัดไป |
| `weather_state` | `"ปกติ"` | |
| `injur_man`, `injur_femel` | `0`, `0` | จำนวนบาดเจ็บ ชาย/หญิง |
| `dead_man`, `dead_femel` | `0`, `0` | จำนวนเสียชีวิต ชาย/หญิง |
| `cause` | `"เปลี่ยนช่องทางกระทันหัน"` | สาเหตุ |

### ⚠️ ไม่มี LATITUDE/LONGITUDE — ต้อง geocode เอง

EXAT ไม่ให้พิกัดมาเลย มีแค่ `expw_step` (ชื่อทางด่วน/ช่วงทาง) เป็น text เช่น
"ศรีรัช", "ฉลองรัช", "เฉลิมมหานคร", "ทางหลวงพิเศษหมายเลข 37"

**การตัดสินใจ:** ทำ manual lookup table map `expw_step` → พิกัดตัวแทนของทางด่วนสายนั้น
(เช่น จุดกึ่งกลางเส้นทาง) เก็บไว้ที่ `dbt/seeds/expw_step_coordinates.csv` (จะสร้างจริงใน
Issue 04/07) ข้อจำกัดที่ต้องรู้ไว้: ความละเอียดของ cluster ฝั่ง EXAT จะหยาบกว่า ARMS มาก
เพราะพิกัดอ้างอิงทั้งทางด่วนเป็นจุดเดียว ไม่ใช่จุดเกิดเหตุจริง — เหมาะกับการบอกว่า
"ทางด่วนสายไหนเสี่ยง" มากกว่า "จุดไหนบนทางด่วนเสี่ยง"

---

## 3. `accident-summary-month` — ใช้ไม่ได้กับ blackspot clustering

- **API:** `https://exat-man.web.app/api/EXAT_AccidentStat/{ปี พ.ศ.}` เช่น `/2564`
- เป็นสถิติสรุปรายเดือนของ EXAT เท่านั้น (จำนวนครั้ง, บาดเจ็บ, เสียชีวิต ต่อเดือน)
- **ไม่มีตำแหน่งจุดเกิดเหตุเลย** — ใช้ประโยชน์ได้แค่เป็นตัวเลขอ้างอิง/validate ผลรวมกับ
  ข้อมูลราย record ของ EXAT_Accident เท่านั้น ไม่เอาเข้า pipeline หลัก

---

## สรุปผลกระทบต่อ Issue ถัดไป

| Issue | ผลกระทบ |
|---|---|
| 04 (Extract) | ARMS = ดึงจาก 4 resource แยกกัน (1 JSON + 3 CSV), ไม่มี loop page; EXAT = loop ปี(พ.ศ.)×เดือน ดึงเฉพาะ `EXAT_Accident` (ไม่ต้องดึง `EXAT_Crash`/`EXAT_TrafficStat*` เพราะไม่เกี่ยวกับ blackspot) |
| 05 (Load raw) | ARMS เองก็มี 2 schema ย่อยในตัว (JSON vs CSV) — ตอน design ตาราง `raw_arms` ควรเก็บทั้ง `source_format` (`json`/`csv`) และ `source_year` ไว้ด้วย เผื่อ debug ย้อนหลังว่า record มาจากไฟล์ไหน |
| 07 (staging) | ต้อง map 3 schema เข้าด้วยกัน ไม่ใช่ 2: (1) ARMS-JSON ตัวพิมพ์ใหญ่ + ISO datetime, (2) ARMS-CSV ตัวพิมพ์เล็ก + วันที่ `D/M/YYYY`, (3) EXAT ตัวพิมพ์เล็ก + `accident_date`/`accident_time` แยก คอลัมน์ severity ก็นับคนละแบบ (ARMS แยกชาย/หญิง/เด็ก, EXAT แยกแค่ชาย/หญิงไม่มีเด็ก) ต้องคิด mapping ให้รอบคอบ |
| 07 (staging) | ต้องเพิ่ม seed table `expw_step_coordinates.csv` สำหรับ geocode ฝั่ง EXAT ก่อนรวมเข้า `stg_accidents` — ตอนนี้ยืนยันแล้วว่าไม่มี endpoint ไหนของ EXAT ให้พิกัดมาเลย ต้องทำ manual lookup จริงๆ (เช่น เปิด Google Maps หาพิกัดกึ่งกลางแต่ละ `expw_step` เอง) |
| 08 (clustering) | cluster ของ EXAT จะหยาบกว่า ARMS มาก (พิกัดอ้างอิงทั้งช่วงทางเป็นจุดเดียว) ควรใส่ column บอก source เพื่อสื่อสารความน่าเชื่อถือที่ต่างกันตอนแสดงผลบนแผนที่ |
| ทั่วไป | ข้อมูลรวมตอนนี้ประมาณ ARMS ~3,083 record (FY2565-2568) + EXAT ต้องดึงดูจริงว่ามีกี่ปีให้ query ได้ (ทดสอบแค่ 2564) — Issue 04 ควรลองไล่ปีอื่นของ EXAT ดูว่า endpoint accept ปีไหนบ้าง |
