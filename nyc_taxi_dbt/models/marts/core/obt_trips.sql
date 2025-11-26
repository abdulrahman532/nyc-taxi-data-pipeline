{{
    config(
        materialized='incremental',
        unique_key='trip_id',
        incremental_strategy='merge',
        cluster_by=['pickup_date', 'pickup_borough']
    )
}}

-- ONE BIG TABLE (OBT): Denormalized wide table for BI tools
-- Pre-joined with all dimensions for fast queries
-- Use this for dashboards, Tableau, Power BI, Looker, etc.

with trips as (
    select * from {{ ref('int_trips_validated') }}
    {% if is_incremental() %}
        where pickup_datetime > (select max(pickup_datetime) from {{ this }})
    {% endif %}
),

zones as (
    select * from {{ ref('dim_zones') }}
),

vendors as (
    select * from {{ ref('dim_vendors') }}
),

payment_types as (
    select * from {{ ref('dim_payment_types') }}
),

rate_codes as (
    select * from {{ ref('dim_rate_codes') }}
)

select
    -- === KEYS ===
    t.trip_id,
    t.vendor_id,
    t.payment_type_id,
    t.rate_code_id,
    t.pickup_location_id,
    t.dropoff_location_id,
    
    -- === TIMESTAMPS ===
    t.pickup_datetime,
    t.dropoff_datetime,
    t.pickup_date,
    t.pickup_month,
    t.pickup_quarter,
    t.pickup_year,
    t.pickup_quarter_num,
    t.pickup_month_num,
    t.pickup_day_of_week,
    t.pickup_hour,
    t.time_of_day,
    t.day_type,
    
    -- === VENDOR (denormalized) ===
    v.vendor_name,
    
    -- === PAYMENT TYPE (denormalized) ===
    pt.payment_type_name,
    
    -- === RATE CODE (denormalized) ===
    rc.rate_code_name,
    
    -- === PICKUP ZONE (denormalized) ===
    pz.borough as pickup_borough,
    pz.zone_name as pickup_zone,
    pz.zone_category as pickup_zone_category,
    pz.is_airport as pickup_is_airport,
    pz.service_zone as pickup_service_zone,
    
    -- === DROPOFF ZONE (denormalized) ===
    dz.borough as dropoff_borough,
    dz.zone_name as dropoff_zone,
    dz.zone_category as dropoff_zone_category,
    dz.is_airport as dropoff_is_airport,
    dz.service_zone as dropoff_service_zone,
    
    -- === TRIP METRICS ===
    t.passenger_count,
    t.trip_distance,
    t.trip_duration_minutes,
    t.store_and_fwd_flag,
    
    -- === FARE BREAKDOWN ===
    t.fare_amount,
    t.extra,
    t.mta_tax,
    t.tip_amount,
    t.tolls_amount,
    t.improvement_surcharge,
    t.congestion_surcharge,
    t.airport_fee,
    t.cbd_congestion_fee,
    t.total_amount,
    
    -- === CALCULATED METRICS ===
    t.fare_per_mile,
    t.speed_mph,
    t.tip_percentage,
    t.has_tolls,
    
    -- === DATA QUALITY FLAGS ===
    t.is_refund,
    t.is_high_fare,
    t.is_very_high_total,
    t.is_generous_tip,
    t.is_no_tip_credit_card,
    t.is_zero_distance_charge,
    t.is_unknown_passenger,
    t.is_large_group,
    t.is_long_duration,
    t.is_fast_trip,
    t.is_slow_trip,
    t.is_high_tolls,
    
    -- === DERIVED FLAGS ===
    pz.is_airport or dz.is_airport as is_airport_trip,
    pz.borough = dz.borough as is_same_borough,
    pz.borough = 'Manhattan' and dz.borough = 'Manhattan' as is_manhattan_to_manhattan,
    pz.borough != dz.borough as is_cross_borough

from trips t
left join zones pz on t.pickup_location_id = pz.location_id
left join zones dz on t.dropoff_location_id = dz.location_id
left join vendors v on t.vendor_id = v.vendor_id
left join payment_types pt on t.payment_type_id = pt.payment_type_id
left join rate_codes rc on t.rate_code_id = rc.rate_code_id
