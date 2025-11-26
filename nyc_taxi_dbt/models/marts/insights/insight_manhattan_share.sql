{{ config(materialized='table') }}

select
    pickup_year, total_trips, manhattan_pickups, manhattan_pct,
    total_trips - manhattan_pickups as outer_borough_pickups,
    round(100 - manhattan_pct, 2) as outer_borough_pct,
    lag(manhattan_pct) over (order by pickup_year) as prev_year_manhattan_pct,
    case when manhattan_pct >= 90 then 'Manhattan Dominance' when manhattan_pct >= 85 then 'Slight Expansion' else 'Diversification' end as market_structure
from {{ ref('agg_yearly') }}
order by pickup_year
