{{ config(materialized='table') }}

-- Uber launched in NYC in 2011, but really started disrupting Yellow Taxi from 2014-2015
-- This model tracks the decline in Yellow Taxi trips that coincides with rideshare growth

with yearly_stats as (
    select * from {{ ref('agg_yearly') }}
),

-- Find the actual peak year dynamically
peak_data as (
    select 
        pickup_year as peak_year,
        total_trips as peak_trips
    from yearly_stats
    order by total_trips desc
    limit 1
)

select
    y.pickup_year,
    y.total_trips,
    y.trips_millions,
    y.trips_yoy_pct,
    y.total_revenue,
    y.revenue_millions,
    p.peak_year,
    p.peak_trips,
    round(y.total_trips * 100.0 / p.peak_trips, 1) as pct_of_peak,
    p.peak_trips - y.total_trips as trips_lost_from_peak,
    round((p.peak_trips - y.total_trips) / 1000000.0, 2) as millions_lost_from_peak,
    
    -- Dynamic era classification based on actual peak year
    case
        when y.pickup_year < p.peak_year then 'Pre-Peak Growth'
        when y.pickup_year = p.peak_year then 'Peak Year'
        when y.pickup_year = p.peak_year + 1 then 'Early Decline'
        when y.pickup_year between p.peak_year + 2 and 2019 then 'Uber Disruption'
        when y.pickup_year = 2020 then 'COVID Crash'
        when y.pickup_year between 2021 and 2023 then 'Recovery Period'
        else 'New Normal'
    end as era,
    
    -- Is this the peak year?
    case when y.pickup_year = p.peak_year then true else false end as is_peak_year,
    
    -- Cumulative loss calculation (only after peak)
    sum(case when y.pickup_year > p.peak_year then p.peak_trips - y.total_trips else 0 end) 
        over (order by y.pickup_year) as cumulative_trips_lost,
    
    -- Year-over-year analysis
    y.avg_fare,
    y.avg_tip_pct,
    y.credit_card_pct,
    y.airport_trip_pct,
    
    -- Market position relative to peak
    case
        when y.pickup_year = p.peak_year then 'Peak Performance'
        when y.total_trips >= p.peak_trips * 0.9 then 'Near Peak'
        when y.total_trips >= p.peak_trips * 0.7 then 'Moderate Decline'
        when y.total_trips >= p.peak_trips * 0.5 then 'Significant Decline'
        when y.total_trips >= p.peak_trips * 0.3 then 'Major Decline'
        else 'Critical Decline'
    end as market_position

from yearly_stats y
cross join peak_data p
order by y.pickup_year
