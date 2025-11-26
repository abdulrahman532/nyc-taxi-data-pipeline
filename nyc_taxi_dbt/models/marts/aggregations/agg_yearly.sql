{{ config(materialized='table') }}

select
    pickup_year,
    sum(total_trips) as total_trips,
    round(sum(total_trips) / 1000000. 0, 2) as trips_millions,
    sum(total_revenue) as total_revenue,
    round(sum(total_revenue) / 1000000.0, 2) as revenue_millions,
    sum(fare_revenue) as fare_revenue,
    sum(tip_revenue) as tip_revenue,
    sum(tolls_revenue) as tolls_revenue,
    sum(congestion_revenue) as congestion_revenue,
    sum(airport_fee_revenue) as airport_fee_revenue,
    sum(cbd_fee_revenue) as cbd_fee_revenue,
    sum(airport_trips) as airport_trips,
    sum(manhattan_pickups) as manhattan_pickups,
    round(avg(avg_fare), 2) as avg_fare,
    round(avg(avg_tip_pct), 2) as avg_tip_pct,
    round(avg(credit_card_pct), 2) as credit_card_pct,
    round(avg(cash_pct), 2) as cash_pct,
    round(avg(airport_trip_pct), 2) as airport_trip_pct,
    round(avg(manhattan_pct), 2) as manhattan_pct,
    lag(sum(total_trips)) over (order by pickup_year) as prev_year_trips,
    round((sum(total_trips) - lag(sum(total_trips)) over (order by pickup_year)) * 100.0 / nullif(lag(sum(total_trips)) over (order by pickup_year), 0), 2) as trips_yoy_pct
from {{ ref('agg_monthly') }}
group by 1
order by 1
