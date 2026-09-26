select
    accident_id,
    accident_date,
    latitude,
    longitude,
    road_name,
    dead_total,
    injured_severe_total,
    injured_light_total,
    source,
    is_geocoded,
    ST_ClusterDBSCAN(
        ST_Transform(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326), 32647),
        eps := 50,
        minpoints := 3
    ) over () as cluster_id
from {{ ref('stg_accidents') }}
