{{ config(materialized='table') }}

select
    location_id,
    borough,
    zone_name,
    service_zone,
    is_yellow_zone,
    is_airport,
    airport_code,
    case 
        when is_airport then 'Airport' 
        when borough = 'Manhattan' then 'Manhattan' 
        else 'Outer Borough' 
    end as zone_category
from {{ ref('stg_taxi_zones') }}
