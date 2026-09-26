with clusters as (

    select
        cluster_id,
        count(*) as n_accidents,
        avg(latitude) as centroid_lat,
        avg(longitude) as centroid_lng,
        sum(dead_total) as dead_total,
        sum(injured_severe_total) as injured_severe_total,
        sum(injured_light_total) as injured_light_total,
        min(accident_date) as first_accident_date,
        max(accident_date) as last_accident_date,
        count(*) filter (where source = 'arms_json') as n_arms_json,
        count(*) filter (where source = 'arms_csv') as n_arms_csv,
        count(*) filter (where source = 'exat') as n_exat,
        bool_or(is_geocoded) as is_geocoded
    from {{ ref('int_accident_clusters') }}
    where cluster_id is not null
    group by cluster_id

),

scored as (

    select
        *,
        (10 * dead_total) + (3 * injured_severe_total) + (1 * injured_light_total) + (2 * n_accidents)
            as severity_score
    from clusters

)

select
    *,
    rank() over (
        partition by is_geocoded
        order by severity_score desc
    ) as rank
from scored
order by is_geocoded, severity_score desc
