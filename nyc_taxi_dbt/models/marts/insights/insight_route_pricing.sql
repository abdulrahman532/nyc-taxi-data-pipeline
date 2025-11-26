{{ config(materialized='table') }}

select
    pickup_zone || ' -> ' || dropoff_zone as route_name,
    pickup_zone, pickup_borough, dropoff_zone, dropoff_borough,
    count(*) as trip_count,
    round(avg(total_amount), 2) as avg_total_fare,
    round(avg(tolls_amount), 2) as avg_tolls,
    round(avg(trip_distance), 2) as avg_distance,
    round(sum(case when has_tolls then 1 else 0 end) * 100.0 / count(*), 1) as pct_with_tolls,
    case when avg(tolls_amount) > 10 then 'High tolls' when dropoff_is_airport or pickup_is_airport then 'Airport trip' when avg(trip_distance) > 15 then 'Long distance' else 'Standard' end as price_driver,
    row_number() over (order by avg(total_amount) desc) as expensive_rank
from {{ ref('obt_trips') }}
group by 1, 2, 3, 4, 5, pickup_is_airport, dropoff_is_airport
having count(*) >= 500
order by avg_total_fare desc
limit 100
