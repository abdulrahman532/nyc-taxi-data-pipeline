{{ config(materialized='table') }}

with yearly as (
    select
        pickup_year,
        sum(total_trips) as annual_trips,
        sum(total_revenue) as annual_revenue,
        avg(avg_trip_revenue) as avg_fare,
        avg(manhattan_pct) as manhattan_share,
        avg(airport_trip_pct) as airport_share,
        avg(credit_card_pct) as credit_card_share
    from {{ ref('agg_monthly_overview') }}
    group by pickup_year
),

with_changes as (
    select
        *,
        lag(annual_trips) over (order by pickup_year) as prev_year_trips,
        round((annual_trips - lag(annual_trips) over (order by pickup_year)) * 100.0 / nullif(lag(annual_trips) over (order by pickup_year), 0), 1) as yoy_trip_change,
        first_value(annual_trips) over (order by pickup_year) as peak_trips
    from yearly
)

select
    pickup_year,
    case 
        when pickup_year in (2013, 2014) then 'Chapter 1: The Golden Era'
        when pickup_year between 2015 and 2019 then 'Chapter 2: The Uber Disruption'
        when pickup_year = 2020 then 'Chapter 3: COVID Collapse'
        when pickup_year between 2021 and 2023 then 'Chapter 4: Uneven Recovery'
        else 'Chapter 5: The New Normal'
    end as story_chapter,
    annual_trips,
    round(annual_trips / 1000000.0, 2) as annual_trips_millions,
    yoy_trip_change as trips_yoy_pct,
    round(annual_trips * 100.0 / peak_trips, 1) as pct_of_peak_volume,
    round(annual_revenue / 1000000.0, 2) as annual_revenue_millions,
    round(avg_fare, 2) as avg_fare,
    round(manhattan_share, 1) as manhattan_share_pct,
    round(airport_share, 1) as airport_share_pct,
    round(credit_card_share, 1) as credit_card_pct,
    case 
        when yoy_trip_change > 5 then 'Growing' 
        when yoy_trip_change between -5 and 5 then 'Stable' 
        when yoy_trip_change between -20 and -5 then 'Declining' 
        else 'Crisis' 
    end as industry_status
from with_changes
order by pickup_year
