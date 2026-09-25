-- รวม stg_arms_json + stg_arms_csv + stg_exat เป็นตารางเดียว (Issue 07 step 6-7)
-- normalize field name ให้ตรงกันหมด, เพิ่ม source/is_geocoded, กรองพิกัดนอกขอบเขตประเทศไทย

with unioned as (

    select
        accident_id::text as accident_id,
        accident_datetime::date as accident_date,
        latitude,
        longitude,
        road_name,
        dead_total,
        injured_severe_total,
        injured_light_total,
        summary,
        'arms_json' as source,
        false as is_geocoded
    from {{ ref('stg_arms_json') }}

    union all

    select
        accident_id::text as accident_id,
        accident_date,
        latitude,
        longitude,
        road_name,
        dead_total,
        injured_severe_total,
        injured_light_total,
        summary,
        'arms_csv' as source,
        false as is_geocoded
    from {{ ref('stg_arms_csv') }}

    union all

    select
        accident_id::text as accident_id,
        accident_date,
        latitude,
        longitude,
        road_name,
        dead_total,
        injured_severe_total,
        injured_light_total,
        summary,
        'exat' as source,
        true as is_geocoded
    from {{ ref('stg_exat') }}

)

select *
from unioned
-- กรองพิกัดผิดปกตินอกขอบเขตประเทศไทย (lat ~5.6-20.5, lng ~97.3-105.6)
where latitude between 5.6 and 20.5
    and longitude between 97.3 and 105.6
