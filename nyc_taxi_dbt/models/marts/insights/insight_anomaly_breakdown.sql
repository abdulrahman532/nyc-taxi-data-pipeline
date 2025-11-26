{{ config(materialized='table') }}

select
    pickup_year,
    count(*) as total_trips,
    sum(case when is_refund then 1 else 0 end) as refund_count,
    round(sum(case when is_refund then 1 else 0 end) * 100.0 / count(*), 3) as refund_pct,
    sum(case when is_high_fare then 1 else 0 end) as high_fare_count,
    sum(case when is_no_tip_credit_card then 1 else 0 end) as no_tip_cc_count,
    round(sum(case when is_no_tip_credit_card then 1 else 0 end) * 100.0 / nullif(sum(case when payment_type_id = 1 then 1 else 0 end), 0), 2) as no_tip_pct_of_cc,
    sum(case when is_zero_distance_charge then 1 else 0 end) as zero_distance_count,
    sum(case when is_unknown_passenger then 1 else 0 end) as unknown_passenger_count,
    sum(case when is_slow_trip then 1 else 0 end) as slow_trip_count
from {{ ref('obt_trips') }}
group by pickup_year
order by pickup_year
