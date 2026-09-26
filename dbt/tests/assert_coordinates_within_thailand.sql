select * from {{ ref('stg_accidents') }}
where latitude not between 5.6 and 20.5
   or longitude not between 97.3 and 105.6
