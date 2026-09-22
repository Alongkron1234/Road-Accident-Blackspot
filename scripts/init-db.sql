-- สร้างฐานข้อมูล warehouse ของโปรเจกต์ (blackspot) แยกจากฐานข้อมูล metadata ของ Airflow
-- (POSTGRES_DB ตัวหลักของ container ถูกใช้เป็น metadata db ของ Airflow ไปแล้ว)
-- idempotent: รันซ้ำได้ไม่ error ถ้า database มีอยู่แล้ว
SELECT 'CREATE DATABASE blackspot'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'blackspot')\gexec
