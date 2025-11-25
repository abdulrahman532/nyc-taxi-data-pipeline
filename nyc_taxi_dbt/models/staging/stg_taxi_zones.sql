{{
    config(materialized='view')
}}

with source as (
    select * from {{ source('raw', 'taxi_zones') }}
)

select
    location_id,
    borough,
    zone_name,
    service_zone,
    case when service_zone = 'Yellow Zone' then true else false end as is_yellow_zone,
    case when service_zone = 'Airports' then true else false end as is_airport,
    case when location_id = 132 then 'JFK' when location_id = 138 then 'LGA' when location_id = 1 then 'EWR' else null end as airport_code
from source
