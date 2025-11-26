{{ config(materialized='table') }}

select
    pickup_quarter, pickup_year, pickup_quarter_num,
    pickup_year || '-Q' || pickup_quarter_num as quarter_label,
    sum(total_trips) as total_trips,
    sum(total_revenue) as total_revenue,
    sum(fare_revenue) as fare_revenue,
    sum(tip_revenue) as tip_revenue,
    sum(airport_trips) as airport_trips,
    round(avg(avg_fare), 2) as avg_fare,
    round(avg(avg_tip_pct), 2) as avg_tip_pct,
    round(avg(credit_card_pct), 2) as credit_card_pct,
    round(avg(airport_trip_pct), 2) as airport_trip_pct,
    round(avg(manhattan_pct), 2) as manhattan_pct,
    lag(sum(total_trips)) over (order by pickup_quarter) as prev_quarter_trips,
    round((sum(total_trips) - lag(sum(total_trips)) over (order by pickup_quarter)) * 100.0 / nullif(lag(sum(total_trips)) over (order by pickup_quarter), 0), 2) as trips_qoq_pct
from {{ ref('agg_monthly') }}
group by 1, 2, 3, 4
order by 1
