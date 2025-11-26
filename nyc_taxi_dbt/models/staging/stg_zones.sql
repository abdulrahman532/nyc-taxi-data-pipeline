{{ config(materialized='view') }}

select
    location_id,
    borough,
    zone_name,
    service_zone,
    case when service_zone = 'Airports' then true when service_zone = 'EWR' then true when location_id in (1, 132, 138) then true else false end as is_airport,
    service_zone = 'Yellow Zone' as is_yellow_zone,
    service_zone = 'Boro Zone' as is_boro_zone,
    case location_id when 1 then 'EWR' when 132 then 'JFK' when 138 then 'LGA' else null end as airport_code
from {{ source('raw', 'taxi_zones') }}
