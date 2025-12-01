select *
from {{ ref('fct_trips') }}
where speed_mph > 100 
   or speed_mph < 0
