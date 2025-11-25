{{
    config(materialized='view')
}}

with trips as (
    select * from {{ ref('int_trips_cleaned') }}
),
pickup_zones as (
    select * from {{ ref('stg_taxi_zones') }}
),
dropoff_zones as (
    select * from {{ ref('stg_taxi_zones') }}
)

select
    t.*,
    pz.borough as pickup_borough,
    pz.zone_name as pickup_zone,
    pz.service_zone as pickup_service_zone,
    pz.is_airport as pickup_is_airport,
    pz.airport_code as pickup_airport_code,
    dz.borough as dropoff_borough,
    dz.zone_name as dropoff_zone,
    dz.service_zone as dropoff_service_zone,
    dz.is_airport as dropoff_is_airport,
    dz.airport_code as dropoff_airport_code,
    case 
        when t.trip_distance > 0 then t.fare_amount / t.trip_distance 
        else 0 
    end as fare_per_mile,
    case 
        when t.trip_duration_minutes > 0 then t.trip_distance / (t.trip_duration_minutes / 60.0) 
        else 0 
    end as avg_speed_mph,
    case 
        when t.fare_amount > 0 and t.payment_type_id = 1 then (t.tip_amount / t.fare_amount) * 100 
        else null 
    end as tip_percentage,
    case 
        when pz.is_airport or dz.is_airport then true 
        else false 
    end as is_airport_trip,
    case 
        when pz.borough = dz.borough then true 
        else false 
    end as is_same_borough,
    t.pickup_location_id || '-' || t.dropoff_location_id as route_id
from trips t
left join pickup_zones pz on t.pickup_location_id = pz.location_id
left join dropoff_zones dz on t.dropoff_location_id = dz.location_id
