{{
    config(
        materialized='incremental',
        unique_key='trip_id',
        incremental_strategy='merge',
        cluster_by=['pickup_date', 'pickup_borough']
    )
}}

with trips as (
    select * from {{ ref('int_trips_enriched') }}
    {% if is_incremental() %}
    where pickup_date > (select max(pickup_date) - interval '{{ var("incremental_lookback_days") }} days' from {{ this }})
    {% endif %}
)

select
    trip_id,
    vendor_id,
    payment_type_id,
    rate_code_id,
    pickup_location_id,
    dropoff_location_id,
    pickup_datetime,
    dropoff_datetime,
    pickup_date,
    pickup_month,
    pickup_year,
    pickup_day_of_week,
    pickup_hour,
    time_of_day,
    day_type,
    trip_duration_minutes,
    passenger_count,
    trip_distance,
    pickup_borough,
    pickup_zone,
    dropoff_borough,
    dropoff_zone,
    route_id,
    is_airport_trip,
    is_same_borough,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    congestion_surcharge,
    airport_fee,
    cbd_congestion_fee,
    total_amount,
    fare_per_mile,
    avg_speed_mph,
    tip_percentage,
    current_timestamp() as _loaded_at
from trips
