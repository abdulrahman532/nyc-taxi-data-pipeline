{{ config(materialized='table') }}

-- Monthly aggregations using the denormalized OBT table
-- This provides all the pre-computed metrics for BI dashboards

select
    pickup_month,
    pickup_year,
    pickup_month_num,
    count(*) as total_trips,
    count(distinct pickup_date) as active_days,
    sum(passenger_count) as total_passengers,
    round(sum(trip_distance), 0) as total_miles,
    round(avg(trip_distance), 2) as avg_distance,
    round(avg(trip_duration_minutes), 2) as avg_duration_min,
    round(avg(speed_mph), 2) as avg_speed_mph,
    round(sum(total_amount), 2) as total_revenue,
    round(sum(fare_amount), 2) as fare_revenue,
    round(sum(tip_amount), 2) as tip_revenue,
    round(sum(tolls_amount), 2) as tolls_revenue,
    round(sum(congestion_surcharge), 2) as congestion_revenue,
    round(sum(airport_fee), 2) as airport_fee_revenue,
    round(sum(cbd_congestion_fee), 2) as cbd_fee_revenue,
    round(avg(total_amount), 2) as avg_fare,
    round(avg(tip_percentage), 2) as avg_tip_pct,
    sum(case when payment_type_id = 1 then 1 else 0 end) as credit_card_trips,
    sum(case when payment_type_id = 2 then 1 else 0 end) as cash_trips,
    round(sum(case when payment_type_id = 1 then 1 else 0 end) * 100.0 / count(*), 2) as credit_card_pct,
    round(sum(case when payment_type_id = 2 then 1 else 0 end) * 100.0 / count(*), 2) as cash_pct,
    sum(case when is_airport_trip then 1 else 0 end) as airport_trips,
    round(sum(case when is_airport_trip then 1 else 0 end) * 100.0 / count(*), 2) as airport_trip_pct,
    sum(case when pickup_borough = 'Manhattan' then 1 else 0 end) as manhattan_pickups,
    round(sum(case when pickup_borough = 'Manhattan' then 1 else 0 end) * 100.0 / count(*), 2) as manhattan_pct,
    sum(case when has_tolls then 1 else 0 end) as trips_with_tolls,
    round(sum(case when has_tolls then 1 else 0 end) * 100.0 / count(*), 2) as tolls_pct,
    sum(case when is_refund then 1 else 0 end) as refund_count,
    sum(case when is_high_fare then 1 else 0 end) as high_fare_count
from {{ ref('obt_trips') }}
group by 1, 2, 3
order by 1