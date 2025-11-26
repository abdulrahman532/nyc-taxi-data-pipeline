{{ config(materialized='view') }}

-- Staging: minimal transformation, keep data as-is from source
-- Note: pickup_datetime might be corrupted, dropoff is stored as microseconds

with source as (
    select 
        *,
        row_number() over (
            partition by tpep_dropoff_datetime, vendorid, pulocationid, dolocationid, fare_amount, trip_distance
            order by tpep_pickup_datetime
        ) as row_num
    from {{ source('raw', 'trips') }}
)

select
    {{ dbt_utils.generate_surrogate_key([
        'tpep_dropoff_datetime', 'vendorid', 'pulocationid', 'dolocationid', 
        'fare_amount', 'trip_distance', 'tip_amount', 'row_num'
    ]) }} as trip_id,
    vendorid as vendor_id,
    pulocationid as pickup_location_id,
    dolocationid as dropoff_location_id,
    ratecodeid as rate_code_id,
    payment_type as payment_type_id,
    -- Pickup: epoch_nanosecond gives 25-digit number, take first 16 digits (microseconds)
    left(date_part(epoch_nanosecond, tpep_pickup_datetime)::varchar, 16)::number as pickup_datetime_raw,
    -- Dropoff is stored as microseconds number (16 digits)
    tpep_dropoff_datetime as dropoff_datetime_raw,
    passenger_count,
    trip_distance,
    store_and_fwd_flag,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    total_amount,
    congestion_surcharge,
    coalesce(airport_fee, 0) as airport_fee,
    coalesce(cbd_congestion_fee, 0) as cbd_congestion_fee
from source
where tpep_dropoff_datetime is not null
