-- Issue 05: สร้างตาราง raw_arms / raw_exat ใน database "blackspot"
-- (ไม่ใช่ docker-entrypoint-initdb.d เพราะ script นั้นรันแค่ครั้งแรกตอน volume ยังไม่มีข้อมูล
-- ส่วนนี้ต้องรันได้ซ้ำๆ ได้เองอิสระ เลยแยกไฟล์ รันด้วย psql เอง)
--
-- Usage:
--   docker compose exec -T postgres psql -U "$POSTGRES_USER" -d blackspot -f - < scripts/create_raw_tables.sql
-- หรือต่อจาก host ตรงๆ ผ่าน psql/DBeaver ที่ port ตาม .env (ดู docs/local_setup.md)

\connect blackspot

CREATE TABLE IF NOT EXISTS raw_arms (
    id            SERIAL PRIMARY KEY,
    source_file   TEXT NOT NULL UNIQUE,
    source_format TEXT NOT NULL CHECK (source_format IN ('json', 'csv')),
    source_year   TEXT NOT NULL,
    payload       JSONB NOT NULL,
    loaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw_exat (
    id            SERIAL PRIMARY KEY,
    source_file   TEXT NOT NULL UNIQUE,
    source_year   INTEGER NOT NULL,
    source_month  INTEGER NOT NULL,
    payload       JSONB NOT NULL,
    loaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
