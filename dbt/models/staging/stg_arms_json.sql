-- แกะ payload ของ raw_arms เฉพาะแถวที่มาจากไฟล์ JSON (accident.json, ปีงบ 2565)
-- field เป็นตัวพิมพ์ใหญ่ทั้งหมด ตามที่บันทึกไว้ใน docs/api_notes.md

select
    (record ->> 'ID')::int as accident_id,
    (record ->> 'ACCIDENT_DATETIME')::timestamptz as accident_datetime,
    (record ->> 'LATITUDE')::float as latitude,
    (record ->> 'LONGITUDE')::float as longitude,
    record ->> 'PROVINCE_NAME' as province_name,
    record ->> 'ROAD_NAME_CRD' as road_name,
    coalesce((record ->> 'DEATH')::int, 0) as dead_total,
    coalesce((record ->> 'WOUNDEDSEVERE')::int, 0) as injured_severe_total,
    coalesce((record ->> 'WOUNDEDLIGHT')::int, 0) as injured_light_total,
    record ->> 'SUMMARY' as summary,
    loaded_at
from {{ source('raw', 'raw_arms') }},
    jsonb_array_elements(payload) as record
where source_format = 'json'
