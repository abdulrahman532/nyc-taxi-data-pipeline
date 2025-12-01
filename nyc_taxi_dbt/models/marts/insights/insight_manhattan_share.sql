{{ config(materialized='view', schema='insights') }}

select
    pickup_year,
    total_trips,
    manhattan_pct,
    round(100 - manhattan_pct, 2) as outer_borough_pct,
    lag(manhattan_pct) over (order by pickup_year) as prev_year_manhattan_pct,
    case
        when manhattan_pct >= 90 then 'Manhattan Monopoly'
        when manhattan_pct >= 80 then 'Manhattan Dominance'
        else 'Diversified Market'
    end as market_structure
from {{ ref('agg_yearly') }}
order by pickup_year