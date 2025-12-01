{{ config(materialized='view', schema='gold') }}

select
    f.*,
    -- Zones
    pz.borough as pickup_borough,
    pz.zone_name as pickup_zone,
    pz.is_airport as pickup_is_airport,
    dz.borough as dropoff_borough,
    dz.zone_name as dropoff_zone,
    dz.is_airport as dropoff_is_airport,

    -- Vendor & Payment
    v.vendor_name,
    pt.payment_type_name,
    rc.rate_code_name,

    -- Derived
    pz.is_airport or dz.is_airport as is_airport_trip,
    pz.borough = 'Manhattan' as is_manhattan_pickup,
    f.is_suspicious_zero_distance or f.is_zero_distance_high_fare as is_potential_fraud

from {{ ref('fct_trips') }} f
left join {{ ref('dim_zones') }} pz on f.pickup_location_id = pz.location_id
left join {{ ref('dim_zones') }} dz on f.dropoff_location_id = dz.location_id
left join {{ ref('dim_vendors') }} v on f.vendor_id = v.vendor_id
left join {{ ref('dim_payment_types') }} pt on f.payment_type_id = pt.payment_type_id
left join {{ ref('dim_rate_codes') }} rc on f.rate_code_id = rc.rate_code_id