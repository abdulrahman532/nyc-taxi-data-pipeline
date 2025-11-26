{{ config(materialized='table') }}

select
    pickup_year, total_trips, trips_millions, total_revenue, revenue_millions,
    first_value(total_trips) over (order by pickup_year) as baseline_2013_trips,
    round(total_trips * 100.0 / first_value(total_trips) over (order by pickup_year), 1) as pct_of_2013,
    trips_yoy_pct,
    case when pickup_year <= 2014 then 'Pre-Uber Era' when pickup_year between 2015 and 2019 then 'Uber Disruption' when pickup_year = 2020 then 'COVID Year' when pickup_year between 2021 and 2023 then 'Recovery Period' else 'New Normal' end as era,
    case pickup_year when 2013 then 'Baseline year' when 2014 then 'Peak year before Uber' when 2015 then 'Uber disruption begins' when 2016 then 'Rideshare grows' when 2017 then 'Short trips lost' when 2018 then 'Stabilization' when 2019 then '50% decline from peak' when 2020 then 'COVID collapse' when 2021 then 'Recovery begins' when 2022 then 'Partial recovery' when 2023 then 'New equilibrium' when 2024 then 'Congestion pricing' when 2025 then 'CBD fee starts' else 'Ongoing' end as year_narrative
from {{ ref('agg_yearly') }}
order by pickup_year
