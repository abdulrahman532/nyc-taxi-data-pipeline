{{
    config(
        materialized='incremental',
        unique_key='pickup_month',
        incremental_strategy='merge'
    )
}}

with trips as (
    select * from {{ ref('fct_trips') }}
    {% if is_incremental() %}
    where pickup_month >= (select max(pickup_month) - interval '2 months' from {{ this }})
    {% endif %}
)

select
    pickup_month,
    pickup_year,
    count(*) as total_trips,
    count(distinct pickup_date) as active_days,
    sum(passenger_count) as total_passengers,
    round(sum(trip_distance), 0) as total_miles,
    round(avg(trip_distance), 2) as avg_distance,
    round(avg(trip_duration_minutes), 2) as avg_duration_min,
    round(sum(total_amount), 2) as total_revenue,
    round(sum(fare_amount), 2) as fare_revenue,
    round(sum(tip_amount), 2) as tip_revenue,
    round(sum(congestion_surcharge), 2) as congestion_revenue,
    round(sum(airport_fee), 2) as airport_fee_revenue,
    round(sum(cbd_congestion_fee), 2) as cbd_fee_revenue,
    round(avg(total_amount), 2) as avg_trip_revenue,
    round(avg(tip_percentage), 2) as avg_tip_pct,
    round(avg(avg_speed_mph), 2) as avg_speed_mph,
    sum(case when payment_type_id = 1 then 1 else 0 end) as credit_card_trips,
    round(sum(case when payment_type_id = 1 then 1 else 0 end) * 100.0 / count(*), 2) as credit_card_pct,
    sum(case when is_airport_trip then 1 else 0 end) as airport_trips,
    round(sum(case when is_airport_trip then 1 else 0 end) * 100.0 / count(*), 2) as airport_trip_pct,
    sum(case when pickup_borough = 'Manhattan' then 1 else 0 end) as manhattan_trips,
    round(sum(case when pickup_borough = 'Manhattan' then 1 else 0 end) * 100.0 / count(*), 2) as manhattan_pct,
    current_timestamp() as _loaded_at
from trips
group by pickup_month, pickup_year
