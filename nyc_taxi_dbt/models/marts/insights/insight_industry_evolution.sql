{{ config(materialized='table') }}

select
    pickup_year, total_trips, trips_millions, trips_yoy_pct, total_revenue, revenue_millions,
    first_value(total_trips) over (order by pickup_year) as baseline_2013_trips,
    round(total_trips * 100.0 / first_value(total_trips) over (order by pickup_year), 1) as pct_of_2013,
    avg_fare, avg_tip_pct, credit_card_pct, cash_pct, airport_trip_pct, manhattan_pct,
    case when pickup_year <= 2014 then 'Golden Era' when pickup_year between 2015 and 2019 then 'Uber Disruption' when pickup_year = 2020 then 'COVID' when pickup_year between 2021 and 2023 then 'Recovery' else 'New Normal' end as era,
    case when pickup_year <= 2014 then 'Ch1: Golden Era' when pickup_year between 2015 and 2019 then 'Ch2: Uber Disruption' when pickup_year = 2020 then 'Ch3: COVID' when pickup_year between 2021 and 2023 then 'Ch4: Recovery' else 'Ch5: New Normal' end as story_chapter,
    case when trips_yoy_pct > 10 then 'Strong Growth' when trips_yoy_pct > 0 then 'Growth' when trips_yoy_pct between -10 and 0 then 'Slight Decline' when trips_yoy_pct < -30 then 'Crisis' else 'Decline' end as industry_health
from {{ ref('agg_yearly') }}
order by pickup_year
