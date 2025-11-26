select *
from {{ ref('fct_trips') }}
where speed_mph > 100
