-- แกะ payload ของ raw_exat, join กับ seed expw_step_coordinates เพื่อเติมพิกัด
-- (EXAT ไม่มี lat/lng มาให้เอง ต้อง geocode เองด้วย lookup table ตามที่บันทึกไว้ใน docs/api_notes.md)
-- _id ไม่ unique ข้ามเดือน/ปี ต้องประกอบ key เองจาก source_year/source_month/_id

select
    source_year::text || '_' || lpad(source_month::text, 2, '0') || '_' || (record ->> '_id') as accident_id,
    (record ->> 'accident_date')::date as accident_date,
    record ->> 'expw_step' as road_name,
    coords.latitude,
    coords.longitude,
    coalesce((record ->> 'dead_man')::int, 0) + coalesce((record ->> 'dead_femel')::int, 0) as dead_total,
    -- EXAT ไม่แยกระดับความรุนแรงของผู้บาดเจ็บ (มีแค่ injur_man/injur_femel รวม) ต่างจาก ARMS
    -- ที่แยก severe/light ชัดเจน จึงไม่รู้ว่าเป็น severe หรือ light จริง ใส่ severe=0 เป็น
    -- ค่า default (ไม่ได้แปลว่าไม่มี severe จริง แค่ไม่มีข้อมูลแยก) แล้วรวมผู้บาดเจ็บทั้งหมด
    -- ไว้ที่ injured_light_total แทน
    0 as injured_severe_total,
    coalesce((record ->> 'injur_man')::int, 0) + coalesce((record ->> 'injur_femel')::int, 0) as injured_light_total,
    record ->> 'cause' as summary,
    loaded_at
from {{ source('raw', 'raw_exat') }},
    jsonb_array_elements(payload) as record
left join {{ ref('expw_step_coordinates') }} as coords
    on coords.expw_step = record ->> 'expw_step'
