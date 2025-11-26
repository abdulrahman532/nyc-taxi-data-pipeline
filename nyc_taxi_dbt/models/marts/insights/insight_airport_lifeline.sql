{{ config(materialized='table') }}

select
    pickup_year, total_trips, trips_millions, airport_trips,
    round(airport_trips / 1000000.0, 2) as airport_trips_millions,
    airport_trip_pct,
    lag(airport_trip_pct) over (order by pickup_year) as prev_year_airport_pct,
    round(airport_trip_pct - lag(airport_trip_pct) over (order by pickup_year), 2) as airport_pct_change,
    total_trips - airport_trips as non_airport_trips,
    case when pickup_year <= 2015 then 'Airport: small portion' when pickup_year between 2016 and 2019 then 'Airport share growing' when pickup_year = 2020 then 'COVID collapse' else 'Airport: critical lifeline' end as insight
from {{ ref('agg_yearly') }}
order by pickup_year
