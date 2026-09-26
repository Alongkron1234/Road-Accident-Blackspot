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
        loaded_at,
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
        loaded_at,
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
        loaded_at,
        'exat' as source,
        true as is_geocoded
    from {{ ref('stg_exat') }}

),

filtered as (

    select *
    from unioned
    where latitude between 5.6 and 20.5
        and longitude between 97.3 and 105.6

),

deduped as (

    select
        *,
        row_number() over (
            partition by accident_id, source
            order by loaded_at desc
        ) as rn
    from filtered

)

select
    accident_id,
    accident_date,
    latitude,
    longitude,
    road_name,
    dead_total,
    injured_severe_total,
    injured_light_total,
    summary,
    source,
    is_geocoded
from deduped
where rn = 1
