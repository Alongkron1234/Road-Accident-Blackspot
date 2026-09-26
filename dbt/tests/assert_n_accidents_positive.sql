select * from {{ ref('mart_blackspot_severity') }}
where n_accidents <= 0
