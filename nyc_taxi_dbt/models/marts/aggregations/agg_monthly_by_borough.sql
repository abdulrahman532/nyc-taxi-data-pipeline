{{
    config(
        materialized='incremental',
        unique_key=['pickup_month', 'pickup_borough'],
        incremental_strategy='merge'
    )
}}

with trips as (
    select * from {{ ref('fct_trips') }}
    {% if is_incremental() %}
    where pickup_month >= (select max(pickup_month) - interval '2 months' from {{ this }})
    {% endif %}
)

select
    pickup_month,
    pickup_year,
    pickup_borough,
    count(*) as total_trips,
    round(sum(total_amount), 2) as total_revenue,
    round(avg(total_amount), 2) as avg_revenue,
    round(avg(trip_distance), 2) as avg_distance,
    round(avg(trip_duration_minutes), 2) as avg_duration,
    sum(case when is_airport_trip then 1 else 0 end) as airport_trips,
    current_timestamp() as _loaded_at
from trips
where pickup_borough is not null
group by pickup_month, pickup_year, pickup_borough
