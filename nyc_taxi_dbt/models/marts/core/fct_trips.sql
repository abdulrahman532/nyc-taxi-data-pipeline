{{
    config(
        materialized='incremental',
        unique_key='trip_id',
        incremental_strategy='merge',
        cluster_by=['pickup_date']
    )
}}

-- FACT TABLE: Clean star schema design
-- Contains only: Keys (FKs) + Degenerate Dimensions + Measures
-- All derived fields and denormalized attributes go to obt_trips

with trips as (
    select * from {{ ref('int_trips_validated') }}
    {% if is_incremental() %}
        where pickup_datetime > (select max(pickup_datetime) from {{ this }})
    {% endif %}
)

select
    -- Primary Key
    trip_id,
    
    -- Foreign Keys (join to dimensions)
    vendor_id,              -- FK → dim_vendors
    payment_type_id,        -- FK → dim_payment_types
    rate_code_id,           -- FK → dim_rate_codes
    pickup_location_id,     -- FK → dim_zones
    dropoff_location_id,    -- FK → dim_zones
    pickup_date,            -- FK → dim_date (date grain for partitioning)
    
    -- Degenerate Dimensions (no separate dim table needed)
    pickup_datetime,
    dropoff_datetime,
    store_and_fwd_flag,
    
    -- Measures (facts/metrics)
    passenger_count,
    trip_distance,
    trip_duration_minutes,
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

from trips
