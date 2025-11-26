-- Test: Pickup must be before dropoff
select *
from {{ ref('fct_trips') }}
where pickup_datetime >= dropoff_datetime
