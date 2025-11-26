{{ config(materialized='table') }}

with trips as (select * from {{ ref('int_trips_validated') }}),
zones as (select * from {{ ref('dim_zones') }})
select
    t.trip_id, t.vendor_id, t. payment_type_id, t.rate_code_id, t.pickup_location_id, t. dropoff_location_id,
    t.pickup_datetime, t. dropoff_datetime, t.pickup_date, t.pickup_month, t.pickup_quarter, t. pickup_year,
    t.pickup_quarter_num, t.pickup_month_num, t.pickup_day_of_week, t.pickup_hour, t.time_of_day, t.day_type,
    t. trip_duration_minutes, t. passenger_count, t. trip_distance, t. store_and_fwd_flag,
    pz.borough as pickup_borough, pz.zone_name as pickup_zone, pz.zone_category as pickup_zone_category, pz.is_airport as pickup_is_airport,
    dz.borough as dropoff_borough, dz.zone_name as dropoff_zone, dz.zone_category as dropoff_zone_category, dz.is_airport as dropoff_is_airport,
    t.fare_amount, t. extra, t.mta_tax, t. tip_amount, t.tolls_amount, t.improvement_surcharge, t. congestion_surcharge, t.airport_fee, t.cbd_congestion_fee, t.total_amount,
    t.fare_per_mile, t.speed_mph, t.tip_percentage, t.has_tolls,
    t.is_refund, t.is_high_fare, t.is_very_high_total, t.is_generous_tip, t.is_no_tip_credit_card, t.is_zero_distance_charge, t.is_unknown_passenger, t. is_large_group, t.is_long_duration, t.is_fast_trip, t.is_slow_trip, t.is_high_tolls,
    pz.is_airport or dz.is_airport as is_airport_trip,
    pz.borough = dz.borough as is_same_borough,
    pz.borough = 'Manhattan' and dz.borough = 'Manhattan' as is_manhattan_to_manhattan
from trips t
left join zones pz on t.pickup_location_id = pz.location_id
left join zones dz on t.dropoff_location_id = dz.location_id
