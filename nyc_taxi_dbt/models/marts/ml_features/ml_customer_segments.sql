{{
    config(
        materialized='incremental',
        unique_key='segment_key',
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
    pickup_location_id || '_' || time_of_day || '_' || day_type || '_' || to_char(pickup_month, 'YYYY-MM') as segment_key,
    pickup_location_id,
    pickup_borough,
    time_of_day,
    day_type,
    pickup_month,
    count(*) as trip_count,
    round(avg(trip_distance), 2) as avg_distance,
    round(avg(trip_duration_minutes), 2) as avg_duration,
    round(avg(total_amount), 2) as avg_fare,
    round(avg(tip_percentage), 2) as avg_tip_pct,
    round(sum(case when payment_type_id = 1 then 1 else 0 end) * 100.0 / count(*), 2) as credit_card_pct,
    round(sum(case when is_airport_trip then 1 else 0 end) * 100.0 / count(*), 2) as airport_trip_pct,
    case 
        when sum(case when is_airport_trip then 1 else 0 end) * 100.0 / count(*) > 50 then 'Airport Traveler'
        when avg(trip_distance) > 10 then 'Long Distance'
        when time_of_day = 'Morning Rush' then 'Commuter'
        when time_of_day = 'Late Night' then 'Night Owl'
        else 'Regular'
    end as preliminary_segment,
    current_timestamp() as _loaded_at
from trips
group by 1, 2, 3, 4, 5, 6
having count(*) >= 10
