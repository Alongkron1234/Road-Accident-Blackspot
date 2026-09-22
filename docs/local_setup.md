# Local Setup — Postgres + Airflow (Docker Compose)

วิธีรัน infrastructure ของโปรเจกต์บนเครื่อง local (Issue 03)

## Prerequisites

- Docker Desktop (หรือ Docker engine + Compose v2) ติดตั้งและเปิดอยู่
- เช็คเวอร์ชันได้ด้วย:
  ```bash
  docker --version
  docker compose version
  ```

## 1. เตรียม `.env`

```bash
cp .env.example .env
```

แล้วเติมค่าอย่างน้อย 3 ตัวนี้ให้เป็นค่าจริง (อย่าปล่อย `change_me`):
- `POSTGRES_PASSWORD`
- `AIRFLOW__CORE__FERNET_KEY` — generate ด้วย:
  ```bash
  python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
  ```
- `AIRFLOW_ADMIN_PASSWORD`

`.env` อยู่ใน `.gitignore` อยู่แล้ว จะไม่ถูก commit

## 2. Start ทุก service

```bash
docker compose up -d
```

รอบแรกจะช้าหน่อย (ดึง image `apache/airflow` ~1-2GB) รอบถัดไปเร็วขึ้นมาก

รอจน `airflow-init` รันจบ (สร้าง Airflow metadata table + user admin) แล้วค่อยเข้าใช้งาน เช็คสถานะได้ด้วย:

```bash
docker compose ps -a
```

`airflow-init` ควรขึ้น `Exited (0)` (รันครั้งเดียวจบ ไม่ใช่ error), ส่วนอีก 3 ตัวควรเป็น `Up`

## 3. เข้าใช้งาน

| Service | URL/วิธีเข้า | Login |
|---|---|---|
| Airflow UI | http://localhost:8081 | user/password ตาม `AIRFLOW_ADMIN_USER`/`AIRFLOW_ADMIN_PASSWORD` ใน `.env` |
| Postgres | `localhost:5433` (จาก host), หรือ `postgres:5432` (จากใน container อื่นในเครือข่ายเดียวกัน) | user/password ตาม `POSTGRES_USER`/`POSTGRES_PASSWORD` ใน `.env` |

⚠️ **Port ไม่ใช่ default 5432/8080** — จงใจเปลี่ยนเป็น **5433**/**8081** เพราะเครื่อง dev อาจมีโปรเจกต์อื่นรัน Postgres/Airflow จับ port default อยู่แล้ว (เจอเคสนี้จริงตอน dev — โปรเจกต์อื่นชื่อ `goldforcast` จับทั้งคู่พอดี) ถ้า 5433/8081 ก็ชนอีก แก้ได้ที่ `POSTGRES_PORT`/`AIRFLOW_WEBSERVER_PORT` ใน `.env`

Postgres มี 2 database แยกกันในตัวเดียวกัน:
- `airflow` — metadata ของ Airflow เอง
- `blackspot` — data warehouse ของโปรเจกต์ (raw/staging/mart layer ตาม ELT ที่วางแผนไว้)

## 4. Airflow Connection ที่เตรียมไว้ให้ DAG ใช้

มี connection ชื่อ `postgres_blackspot` สร้างไว้แล้ว ชี้ไปที่ database `blackspot` (host ภายใน docker network คือ `postgres`, ไม่ใช่ `localhost`) — DAG ใน Issue 06 เป็นต้นไปเรียกใช้ connection นี้ได้เลยโดยไม่ต้องสร้างใหม่

ถ้าต้องสร้างใหม่ (เช่น รัน `docker compose down -v` ที่ล้าง volume ทิ้งหมด):
```bash
docker compose exec airflow-webserver airflow connections add 'postgres_blackspot' \
  --conn-type 'postgres' \
  --conn-host 'postgres' \
  --conn-port '5432' \
  --conn-schema 'blackspot' \
  --conn-login "$POSTGRES_USER" \
  --conn-password "$POSTGRES_PASSWORD"
```

⚠️ **อย่ารันคำสั่งเช็ค connection ด้วย `-o table`** (เช่น `airflow connections get postgres_blackspot -o table`) เพราะจะ print password ออกมาเป็น plain text ในหน้าจอ/log ใช้ `airflow connections list` (ไม่โชว์ password) หรือเช็คด้วยการต่อ database ตรงๆ ด้วย `psycopg2`/`psql` แทน

## 5. คำสั่งที่ใช้บ่อย

```bash
docker compose ps -a              # ดูสถานะทุก container
docker compose logs -f <service>  # ดู log แบบ real-time เช่น airflow-scheduler
docker compose down                # หยุดทุก container (เก็บข้อมูลใน volume ไว้)
docker compose down -v             # หยุด + ลบ volume ทิ้งหมด (ข้อมูลหายถาวร รวมถึง Airflow metadata)
docker compose up -d               # start ใหม่ (หรือ recreate container ที่ config/env เปลี่ยน)
```

**ถ้าเปลี่ยน `.env`** (เช่น rotate password) ต้อง `docker compose up -d` ใหม่เสมอ ไม่งั้น container ที่รันอยู่จะยังใช้ค่าเก่าที่ฝังไว้ตอน start ค้างอยู่ — จะเจอ error แบบ `password authentication failed` ถ้าเปลี่ยน password แล้วลืม restart

## 6. Troubleshooting

**`Bind for 0.0.0.0:5432 failed: port is already allocated`**
มีโปรแกรม/container อื่นจับ port 5432 (หรือ 8080) อยู่แล้ว เช็คด้วย:
```bash
lsof -nP -iTCP:5432 -sTCP:LISTEN
docker ps -a
```
แก้โดยเปลี่ยน `POSTGRES_PORT`/`AIRFLOW_WEBSERVER_PORT` ใน `.env` เป็นเลขอื่นที่ว่าง (โปรเจกต์นี้ default เป็น 5433/8081 อยู่แล้วเพื่อเลี่ยงปัญหานี้)

**Airflow container error `password authentication failed`**
Password ใน Postgres กับที่ container ใช้เชื่อมต่อไม่ตรงกัน (มักเกิดหลัง rotate password ใน `.env` แต่ยังไม่ restart) แก้ด้วย `docker compose up -d`
