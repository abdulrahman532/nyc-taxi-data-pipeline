{{ config(materialized='table') }}

with monthly as (
    select * from {{ ref('agg_monthly_overview') }}
),

with_period as (
    select
        *,
        case 
            when pickup_month < '2020-03-01' then 'Pre-COVID'
            when pickup_month between '2020-03-01' and '2020-06-30' then 'COVID Lockdown'
            when pickup_month between '2020-07-01' and '2021-06-30' then 'Partial Recovery'
            when pickup_month between '2021-07-01' and '2022-12-31' then 'Recovery Phase'
            else 'New Normal'
        end as covid_period
    from monthly
)

select
    pickup_month,
    pickup_year,
    covid_period,
    total_trips,
    total_revenue,
    avg_trip_revenue,
    credit_card_pct,
    airport_trip_pct,
    manhattan_pct,
    avg_distance,
    avg_speed_mph
from with_period
order by pickup_month
