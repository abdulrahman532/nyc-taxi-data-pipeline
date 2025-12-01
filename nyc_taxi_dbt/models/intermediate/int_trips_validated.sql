{{ config(materialized='table', schema='silver') }}

with source as (
    select * from {{ ref('stg_trips') }}
),

cleaned as (
    select
        -- Keys & Raw
        trip_id,
        vendor_id,
        payment_type_id,
        rate_code_id,
        pickup_location_id,
        dropoff_location_id,
        store_and_fwd_flag,

        -- Timestamps
        to_timestamp(pickup_datetime_raw / 1000000)  as pickup_datetime,
        to_timestamp(dropoff_datetime_raw / 1000000) as dropoff_datetime,

        -- Basic metrics
        passenger_count,
        trip_distance,
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        improvement_surcharge,
        congestion_surcharge,
        airport_fee,
        cbd_congestion_fee,
        total_amount
    from source
    where pickup_datetime_raw is not null
      and dropoff_datetime_raw is not null
      and dropoff_datetime_raw >= pickup_datetime_raw
      and pickup_location_id between 1 and 265
      and dropoff_location_id between 1 and 265
),

enhanced as (
    select
        *,
        date(pickup_datetime) as pickup_date,
        date_trunc('month', pickup_datetime)::date as pickup_month,
        year(pickup_datetime) as pickup_year,

        datediff('minute', pickup_datetime, dropoff_datetime) as trip_duration_minutes,

        case when trip_distance > 0 then fare_amount / trip_distance end as fare_per_mile,
        case when datediff('minute', pickup_datetime, dropoff_datetime) > 0 
             then trip_distance / (datediff('minute', pickup_datetime, dropoff_datetime) / 60.0) 
             end as speed_mph,

        case when fare_amount > 0 and payment_type_id = 1 
             then round(tip_amount / fare_amount * 100, 2) end as tip_percentage,

        -- Time of day
        case
            when hour(pickup_datetime) between 6 and 9  then 'Morning Rush'
            when hour(pickup_datetime) between 16 and 19 then 'Evening Rush'
            when hour(pickup_datetime) between 20 and 23 then 'Night'
            when hour(pickup_datetime) between 0 and 5  then 'Late Night'
            else 'Daytime'
        end as time_of_day,

        case when dayofweek(pickup_datetime) in (1,7) then 'Weekend' else 'Weekday' end as day_type,

        -- Strong fraud / anomaly flags
        trip_distance = 0 and fare_amount > 20 and trip_duration_minutes > 10 
            as is_suspicious_zero_distance,

        trip_distance = 0 and fare_amount > 8 
            as is_zero_distance_high_fare,

        fare_amount < 0 
            as is_refund,

        total_amount > 300 
            as is_extreme_fare,

        speed_mph > 80 and trip_duration_minutes > 5
            as is_extreme_speed

    from cleaned
)

select * from enhanced