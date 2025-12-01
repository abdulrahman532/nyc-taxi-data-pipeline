{{ config(materialized='view', schema='insights') }}

with pickup_stats as (
    select
        pickup_location_id as location_id,
        count(*) as pickup_count,
        sum(total_amount) as pickup_revenue,
        avg(total_amount) as avg_fare,
        avg(tip_percentage) filter (where payment_type_id = 1) as avg_tip_pct
    from {{ ref('obt_trips') }}
    group by 1
),
dropoff_stats as (
    select dropoff_location_id as location_id, count(*) as dropoff_count
    from {{ ref('obt_trips') }}
    group by 1
)

select
    z.location_id,
    z.borough,
    z.zone_name,
    z.zone_category,
    z.is_airport,
    coalesce(p.pickup_count, 0) as total_pickups,
    coalesce(p.pickup_revenue, 0) as pickup_revenue,
    round(coalesce(p.avg_fare, 0), 2) as avg_pickup_fare,
    round(coalesce(p.avg_tip_pct, 0), 2) as avg_tip_pct,
    coalesce(d.dropoff_count, 0) as total_dropoffs,
    coalesce(p.pickup_count, 0) + coalesce(d.dropoff_count, 0) as total_activity,
    percent_rank() over (order by coalesce(p.pickup_count, 0) desc) as pickup_percentile,
    case
        when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.95 then 'Very Hot'
        when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.80 then 'Hot'
        when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.50 then 'Warm'
        else 'Cold'
    end as heat_level,
    row_number() over (order by coalesce(p.pickup_count, 0) desc) as pickup_rank
from {{ ref('dim_zones') }} z
left join pickup_stats p on z.location_id = p.location_id
left join dropoff_stats d on z.location_id = d.location_id
order by total_pickups desc