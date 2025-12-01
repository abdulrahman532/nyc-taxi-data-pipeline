{{ config(materialized='view', schema='insights') }}

with yearly as (select * from {{ ref('agg_yearly') }}),
peak as (
    select
        pickup_year as peak_year,
        total_trips as peak_trips
    from yearly
    order by total_trips desc
    limit 1
)

select
    y.*,
    p.peak_year,
    p.peak_trips,
    round(y.total_trips * 100.0 / p.peak_trips, 1) as pct_of_peak,
    p.peak_trips - y.total_trips as trips_lost_from_peak,
    round((p.peak_trips - y.total_trips) / 1000000.0, 2) as millions_lost_from_peak,
    case
        when y.pickup_year = p.peak_year then 'Peak Year'
        when y.pickup_year = 2020 then 'COVID Crash'
        when y.pickup_year > p.peak_year + 5 then 'New Normal'
        else 'Post-Peak Decline'
    end as era
from yearly y
cross join peak p
order by y.pickup_year