{{ config(materialized='view', schema='insights') }}

select
    pickup_year,
    total_trips,
    airport_trips,
    round(airport_trips * 100.0 / total_trips, 2) as airport_share_pct,
    lag(round(airport_trips * 100.0 / total_trips, 2)) over (order by pickup_year) as prev_year_share,
    case
        when pickup_year <= 2015 then 'Airport: Minor Role'
        when pickup_year = 2020 then 'COVID Collapse'
        else 'Airport: Industry Lifeline'
    end as narrative
from {{ ref('agg_yearly') }}
order by pickup_year