{{
    config(
        materialized='incremental',
        unique_key='trip_id',
        incremental_strategy='merge',
        cluster_by=['pickup_date']
    )
}}

with trips as (
    select * from {{ ref('fct_trips') }}
    {% if is_incremental() %}
    where pickup_date > (select max(pickup_date) - interval '{{ var("incremental_lookback_days") }} days' from {{ this }})
    {% endif %}
),

zone_stats as (
    select
        route_id,
        avg(fare_amount) as route_avg_fare,
        stddev(fare_amount) as route_std_fare,
        avg(trip_duration_minutes) as route_avg_duration,
        count(*) as route_trip_count
    from {{ ref('fct_trips') }}
    group by route_id
    having count(*) >= 100
)

select
    t.trip_id,
    t.pickup_date,
    t.vendor_id,
    t.payment_type_id,
    t.pickup_location_id,
    t.dropoff_location_id,
    t.pickup_borough,
    t.pickup_hour,
    t.day_type,
    t.passenger_count,
    t.trip_distance,
    t.trip_duration_minutes,
    t.fare_amount,
    t.tip_amount,
    t.total_amount,
    t.fare_per_mile,
    t.avg_speed_mph,
    t.is_airport_trip,
    
    -- Anomaly detection features
    case 
        when zs.route_std_fare > 0 then (t.fare_amount - zs.route_avg_fare) / zs.route_std_fare 
        else null 
    end as fare_zscore,
    case when t.trip_distance < 0.1 and t.fare_amount > 10 then 1 else 0 end as flag_short_distance_high_fare,
    case when t.avg_speed_mph > 60 then 1 else 0 end as flag_unrealistic_speed,
    case when t.avg_speed_mph < 3 and t.trip_distance > 1 then 1 else 0 end as flag_too_slow,
    case when t.fare_per_mile > 20 then 1 else 0 end as flag_high_fare_per_mile,
    
    -- Anomaly score
    (case when t.trip_distance < 0.1 and t.fare_amount > 10 then 1 else 0 end +
     case when t.avg_speed_mph > 60 then 1 else 0 end +
     case when t.avg_speed_mph < 3 and t.trip_distance > 1 then 1 else 0 end +
     case when t.fare_per_mile > 20 then 1 else 0 end) as anomaly_flag_count,
    
    -- Route statistics
    zs.route_avg_fare,
    zs.route_trip_count,
    
    current_timestamp() as _loaded_at

from trips t
left join zone_stats zs on t.route_id = zs.route_id
