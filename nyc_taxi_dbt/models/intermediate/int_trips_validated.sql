{{ config(materialized='view') }}

with staged as (
    select * from {{ ref('stg_trips') }}
),

with_calculations as (
    select
        *,
        datediff('minute', pickup_datetime, dropoff_datetime) as trip_duration_minutes,
        date(pickup_datetime) as pickup_date,
        date_trunc('month', pickup_datetime)::date as pickup_month,
        date_trunc('quarter', pickup_datetime)::date as pickup_quarter,
        year(pickup_datetime) as pickup_year,
        quarter(pickup_datetime) as pickup_quarter_num,
        month(pickup_datetime) as pickup_month_num,
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
        end as day_type,
        case 
            when trip_distance > 0 then fare_amount / trip_distance 
            else null 
        end as fare_per_mile,
        case 
            when datediff('minute', pickup_datetime, dropoff_datetime) > 0 
            then trip_distance / (datediff('minute', pickup_datetime, dropoff_datetime) / 60.0) 
            else null 
        end as speed_mph,
        case 
            when fare_amount > 0 and payment_type_id = 1 
            then (tip_amount / fare_amount) * 100 
            else null 
        end as tip_percentage,
        case when tolls_amount > 0 then true else false end as has_tolls
    from staged
),

with_flags as (
    select
        *,
        case when fare_amount < 0 then true else false end as is_refund,
        case when fare_amount > 200 then true else false end as is_high_fare,
        case when total_amount > 300 then true else false end as is_very_high_total,
        case when tip_percentage > 30 then true else false end as is_generous_tip,
        case when tip_amount = 0 and payment_type_id = 1 then true else false end as is_no_tip_credit_card,
        case when trip_distance = 0 and fare_amount > 0 then true else false end as is_zero_distance_charge,
        case when passenger_count = 0 or passenger_count is null then true else false end as is_unknown_passenger,
        case when passenger_count > 6 then true else false end as is_large_group,
        case when trip_duration_minutes > 120 then true else false end as is_long_duration,
        case when speed_mph > 50 then true else false end as is_fast_trip,
        case when speed_mph < 5 and trip_distance > 1 then true else false end as is_slow_trip,
        case when tolls_amount > 20 then true else false end as is_high_tolls
    from with_calculations
)

select * from with_flags
where 
    pickup_datetime is not null 
    and dropoff_datetime is not null 
    and dropoff_datetime > pickup_datetime 
    and trip_duration_minutes > 0 
    and trip_duration_minutes <= 1440 
    and (speed_mph is null or speed_mph <= 100) 
    and pickup_location_id between 1 and 265 
    and dropoff_location_id between 1 and 265 
    and pickup_datetime >= '2013-01-01' 
    and pickup_datetime < current_date()
