{{ config(materialized='view', schema='insights') }}

select
    pickup_year,
    count(*) as total_trips,
    sum(case when is_potential_fraud then 1 else 0 end) as fraud_suspect_trips,
    sum(case when is_refund then 1 else 0 end) as refund_trips,
    sum(case when is_extreme_speed then 1 else 0 end) as extreme_speed_trips,
    sum(case when trip_distance = 0 and fare_amount > 0 then 1 else 0 end) as zero_distance_trips,
    round(sum(case when is_potential_fraud then 1 else 0 end) * 100.0 / count(*), 3) as fraud_pct
from {{ ref('obt_trips') }}
group by pickup_year
order by pickup_year