{{ config(materialized='table', schema='gold') }}

with yearly_base as (
    select
        pickup_year,
        sum(total_trips) as total_trips,
        sum(airport_trips) as airport_trips,
        round(sum(total_revenue), 0) as total_revenue,
        round(avg(avg_fare), 2) as avg_fare,
        round(avg(avg_tip_pct_credit_only), 2) as avg_tip_pct_credit_only,
        round(avg(credit_card_pct), 2) as credit_card_pct,
        round(avg(airport_trip_pct), 2) as airport_trip_pct,
        round(avg(manhattan_pct), 2) as manhattan_pct
    from {{ ref('agg_monthly') }}
    group by pickup_year
)

select
    *,
    round(
        (total_trips - lag(total_trips) over (order by pickup_year)) 
        * 100.0 / nullif(lag(total_trips) over (order by pickup_year), 0), 
        2
    ) as trips_yoy_pct
from yearly_base
order by pickup_year