select *
from {{ ref('fct_trips') }}
where fare_amount < -100
