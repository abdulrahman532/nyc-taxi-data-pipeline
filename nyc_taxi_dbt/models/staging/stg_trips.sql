{{
    config(materialized='view')
}}

with source as (
    select * from {{ source('raw', 'trips') }}
),

renamed as (
    select
        {{ dbt_utils.generate_surrogate_key(['tpep_pickup_datetime', 'vendorid', 'pulocationid', 'dolocationid', 'fare_amount', 'trip_distance']) }} as trip_id,
        vendorid as vendor_id,
        tpep_pickup_datetime as pickup_datetime,
        case 
            when tpep_dropoff_datetime is null then null
            when tpep_dropoff_datetime > 1000000000000 then to_timestamp(tpep_dropoff_datetime / 1000000)
            else to_timestamp(tpep_dropoff_datetime)
        end as dropoff_datetime,
        passenger_count,
        trip_distance,
        ratecodeid as rate_code_id,
        store_and_fwd_flag,
        pulocationid as pickup_location_id,
        dolocationid as dropoff_location_id,
        payment_type as payment_type_id,
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
    from source
    where tpep_pickup_datetime is not null
)

select * from renamed
