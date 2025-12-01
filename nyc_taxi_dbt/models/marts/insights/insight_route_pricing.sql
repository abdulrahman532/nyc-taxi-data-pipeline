{{ config(materialized='view', schema='insights') }}

select
    pickup_zone || ' → ' || dropoff_zone as route_name,
    pickup_zone,
    pickup_borough,
    dropoff_zone,
    dropoff_borough,
    count(*) as trip_count,
    round(avg(total_amount), 2) as avg_total_fare,
    round(avg(trip_distance), 2) as avg_distance_miles,
    round(avg(tolls_amount), 2) as avg_tolls,
    round(sum(case when is_airport_trip then 1 else 0 end) * 100.0 / count(*), 1) as airport_pct,
    row_number() over (order by avg(total_amount) desc) as expensive_rank
from {{ ref('obt_trips') }}
group by 1,2,3,4,5
having count(*) >= 500
order by avg_total_fare desc
limit 100