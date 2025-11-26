{{ config(materialized='table') }}

-- Uber launched in NYC in 2011, but really started disrupting Yellow Taxi from 2014-2015
-- This model tracks the decline in Yellow Taxi trips that coincides with rideshare growth

with yearly_stats as (
    select * from {{ ref('agg_yearly') }}
),

peak_year as (
    select max(total_trips) as peak_trips
    from yearly_stats
    where pickup_year <= 2014
)

select
    y.pickup_year,
    y.total_trips,
    y.trips_millions,
    y.trips_yoy_pct,
    y.total_revenue,
    y.revenue_millions,
    p.peak_trips as peak_2014_trips,
    round(y.total_trips * 100.0 / p.peak_trips, 1) as pct_of_peak,
    p.peak_trips - y.total_trips as trips_lost_from_peak,
    round((p.peak_trips - y.total_trips) / 1000000.0, 2) as millions_lost_from_peak,
    
    -- Era classification based on Uber impact
    case
        when y.pickup_year <= 2013 then 'Pre-Uber Era'
        when y.pickup_year = 2014 then 'Peak Year'
        when y.pickup_year between 2015 and 2016 then 'Early Disruption'
        when y.pickup_year between 2017 and 2019 then 'Full Disruption'
        when y.pickup_year = 2020 then 'COVID + Uber'
        else 'Post-COVID Rideshare World'
    end as uber_era,
    
    -- Cumulative loss calculation
    sum(case when y.pickup_year > 2014 then p.peak_trips - y.total_trips else 0 end) 
        over (order by y.pickup_year) as cumulative_trips_lost,
    
    -- Year-over-year analysis
    y.avg_fare,
    y.avg_tip_pct,
    y.credit_card_pct,
    y.airport_trip_pct,
    
    -- Market share insight (assuming Uber took what Yellow lost)
    case
        when y.pickup_year <= 2014 then 'Yellow Taxi Monopoly'
        when y.total_trips >= p.peak_trips * 0.8 then 'Minor Uber Impact'
        when y.total_trips >= p.peak_trips * 0.5 then 'Significant Uber Impact'
        when y.total_trips >= p.peak_trips * 0.3 then 'Uber Dominant'
        else 'Yellow Taxi Niche Player'
    end as market_position

from yearly_stats y
cross join peak_year p
order by y.pickup_year
