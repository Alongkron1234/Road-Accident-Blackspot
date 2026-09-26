select * from {{ ref('mart_blackspot_severity') }}
where severity_score < 0
