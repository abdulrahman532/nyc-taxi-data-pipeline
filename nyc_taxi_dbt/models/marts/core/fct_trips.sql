{{ config(
    materialized='incremental',
    unique_key='trip_id',
    incremental_strategy='merge',
    schema='gold',
    cluster_by=['pickup_date']
) }}

with trips as (
    select * from {{ ref('int_trips_validated') }}
    {% if is_incremental() %}
    where pickup_date >= (select dateadd(day, -7, max(pickup_date)) from {{ this }})
    {% endif %}
)

select
    trip_id,
    vendor_id,
    payment_type_id,
    rate_code_id,
    pickup_location_id,
    dropoff_location_id,
    pickup_date,
    pickup_month,
    pickup_year,

    pickup_datetime,
    dropoff_datetime,
    store_and_fwd_flag,

    passenger_count,
    trip_distance,
    trip_duration_minutes,
    speed_mph,
    fare_per_mile,
    fare_amount, extra, mta_tax, tip_amount, tolls_amount,
    improvement_surcharge, congestion_surcharge, airport_fee, cbd_congestion_fee,
    total_amount,
    
    -- Derived metrics
    tip_percentage,
    time_of_day,
    day_type,
    
    -- Flags
    is_suspicious_zero_distance,
    is_zero_distance_high_fare,
    is_refund,
    is_extreme_fare,
    is_extreme_speed
from trips