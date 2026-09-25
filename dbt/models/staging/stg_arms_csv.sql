-- แกะ payload ของ raw_arms เฉพาะแถวที่มาจากไฟล์ CSV (ปีงบ 2566/2567/2568)
-- field เป็นตัวพิมพ์เล็ก, accident_date เป็น format D/M/YYYY (ไม่ใช่ ISO เหมือน JSON)
-- แยกจำนวนตาย/บาดเจ็บเป็นชาย/หญิง/เด็กชาย/เด็กหญิง ต้องรวมเป็น total เอง (JSON มีแค่ตัวเลขรวม)

select
    (record ->> 'id')::int as accident_id,
    to_date(record ->> 'accident_date', 'FMDD/FMMM/YYYY') as accident_date,
    (record ->> 'latitude')::float as latitude,
    (record ->> 'longitude')::float as longitude,
    record ->> 'road_name' as road_name,
    (
        coalesce((record ->> 'dead_men')::int, 0)
        + coalesce((record ->> 'dead_women')::int, 0)
        + coalesce((record ->> 'dead_child_men')::int, 0)
        + coalesce((record ->> 'dead_child_women')::int, 0)
    ) as dead_total,
    coalesce((record ->> 'injury_severe_total')::int, 0) as injured_severe_total,
    coalesce((record ->> 'injury_less_total')::int, 0) as injured_light_total,
    record ->> 'crash_pattern' as summary
from {{ source('raw', 'raw_arms') }},
    jsonb_array_elements(payload) as record
where source_format = 'csv'
