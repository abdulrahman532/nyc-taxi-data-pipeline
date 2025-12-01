{{ config(materialized='table', schema='gold') }}

select
    pickup_month,
    pickup_year,
    to_char(pickup_month, 'Month') as month_name,

    count(*) as total_trips,
    count(distinct pickup_date) as active_days,

    sum(passenger_count) as total_passengers,
    round(sum(trip_distance), 0) as total_miles,
    round(avg(trip_distance), 2) as avg_distance_miles,

    round(avg(trip_duration_minutes), 2) as avg_duration_minutes,
    round(avg(speed_mph) filter (where speed_mph > 0), 2) as avg_speed_mph,

    round(sum(total_amount), 2) as total_revenue,
    round(avg(total_amount), 2) as avg_fare,

    -- Tips (الأهم)
    round(avg(tip_percentage) filter (where payment_type_id = 1), 2) as avg_tip_pct_credit_only,
    round(sum(tip_amount) filter (where payment_type_id = 1), 2) as total_tip_revenue,

    -- Payment
    sum(case when payment_type_id = 1 then 1 else 0 end) as credit_card_trips,
    round(100.0 * sum(case when payment_type_id = 1 then 1 else 0 end) / count(*), 2) as credit_card_pct,

    -- Geography
    sum(case when is_airport_trip then 1 else 0 end) as airport_trips,
    round(100.0 * sum(case when is_airport_trip then 1 else 0 end) / count(*), 2) as airport_trip_pct,

    sum(case when pickup_borough = 'Manhattan' then 1 else 0 end) as manhattan_pickups,
    round(100.0 * sum(case when pickup_borough = 'Manhattan' then 1 else 0 end) / count(*), 2) as manhattan_pct,

    -- Fraud & Quality
    sum(case when is_potential_fraud then 1 else 0 end) as potential_fraud_trips,
    sum(case when is_refund then 1 else 0 end) as refund_trips,
    
    -- Fee revenues (for insight_fee_impact)
    round(sum(congestion_surcharge), 2) as congestion_revenue,
    round(sum(airport_fee), 2) as airport_fee_revenue,
    round(sum(cbd_congestion_fee), 2) as cbd_fee_revenue

from {{ ref('obt_trips') }}
group by pickup_month, pickup_year
order by pickup_month