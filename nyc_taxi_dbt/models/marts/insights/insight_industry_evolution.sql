{{ config(materialized='view', schema='insights') }}

select
    pickup_year,
    total_trips,
    round(total_trips / 1000000.0, 2) as trips_millions,
    trips_yoy_pct,
    avg_fare,
    avg_tip_pct_credit_only as avg_tip_pct,
    credit_card_pct,
    airport_trip_pct,
    manhattan_pct,
    case
        when pickup_year <= 2014 then 'Golden Era'
        when pickup_year between 2015 and 2019 then 'Uber Disruption'
        when pickup_year = 2020 then 'COVID Crisis'
        when pickup_year between 2021 and 2023 then 'Recovery'
        else 'New Normal'
    end as industry_era
from {{ ref('agg_yearly') }}
order by pickup_year