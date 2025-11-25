{{
    config(materialized='view')
}}

with staged as (
    select * from {{ ref('stg_trips') }}
)

select
    trip_id,
    vendor_id,
    pickup_datetime,
    dropoff_datetime,
    datediff('minute', pickup_datetime, dropoff_datetime) as trip_duration_minutes,
    case 
        when passenger_count is null or passenger_count = 0 then 1 
        when passenger_count > 6 then 6 
        else passenger_count::int 
    end as passenger_count,
    trip_distance,
    rate_code_id,
    store_and_fwd_flag,
    pickup_location_id,
    dropoff_location_id,
    payment_type_id,
    abs(coalesce(fare_amount, 0)) as fare_amount,
    abs(coalesce(extra, 0)) as extra,
    abs(coalesce(mta_tax, 0)) as mta_tax,
    abs(coalesce(tip_amount, 0)) as tip_amount,
    abs(coalesce(tolls_amount, 0)) as tolls_amount,
    abs(coalesce(improvement_surcharge, 0)) as improvement_surcharge,
    abs(coalesce(total_amount, 0)) as total_amount,
    abs(coalesce(congestion_surcharge, 0)) as congestion_surcharge,
    abs(coalesce(airport_fee, 0)) as airport_fee,
    abs(coalesce(cbd_congestion_fee, 0)) as cbd_congestion_fee,
    date(pickup_datetime) as pickup_date,
    date_trunc('month', pickup_datetime)::date as pickup_month,
    year(pickup_datetime) as pickup_year,
    dayofweek(pickup_datetime) as pickup_day_of_week,
    hour(pickup_datetime) as pickup_hour,
    case 
        when hour(pickup_datetime) between 6 and 9 then 'Morning Rush' 
        when hour(pickup_datetime) between 10 and 15 then 'Midday' 
        when hour(pickup_datetime) between 16 and 19 then 'Evening Rush' 
        when hour(pickup_datetime) between 20 and 23 then 'Night' 
        else 'Late Night' 
    end as time_of_day,
    case 
        when dayofweek(pickup_datetime) in (0, 6) then 'Weekend' 
        else 'Weekday' 
    end as day_type
from staged
where pickup_datetime is not null
    and dropoff_datetime is not null
    and dropoff_datetime > pickup_datetime
    and datediff('minute', pickup_datetime, dropoff_datetime) between 1 and 1440
    and trip_distance >= 0 and trip_distance <= 200
    and abs(fare_amount) <= 1000
    and pickup_location_id between 1 and 265
    and dropoff_location_id between 1 and 265
    and pickup_datetime >= '2013-01-01'
