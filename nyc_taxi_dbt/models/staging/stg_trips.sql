{{ config(materialized='view', schema='bronze') }}

select
    {{ dbt_utils.generate_surrogate_key([
        'tpep_pickup_datetime',
        'tpep_dropoff_datetime',
        'vendorid',
        'pulocationid',
        'dolocationid',
        'trip_distance',
        'fare_amount',
        'total_amount'
    ]) }} as trip_id,

    vendorid               as vendor_id,
    pulocationid           as pickup_location_id,
    dolocationid           as dropoff_location_id,
    ratecodeid             as rate_code_id,
    payment_type           as payment_type_id,

    left(date_part(epoch_nanosecond, tpep_pickup_datetime)::varchar, 16)::bigint as pickup_datetime_raw,
    left(date_part(epoch_nanosecond, tpep_dropoff_datetime)::varchar, 16)::bigint as dropoff_datetime_raw,

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
    airport_fee,
    cbd_congestion_fee

from {{ source('raw', 'trips') }}
where tpep_dropoff_datetime is not null