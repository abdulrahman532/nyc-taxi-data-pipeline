{{ config(materialized='view', schema='bronze') }}

select
    location_id,
    borough,
    zone as zone_name,
    service_zone,
    
   
    location_id in (1, 132, 138) as is_airport,
    
    -- Airport codes
    case location_id
        when 1   then 'EWR'
        when 132 then 'JFK'
        when 138 then 'LGA'
        else null
    end as airport_code,

    service_zone = 'Yellow Zone' as is_yellow_zone,
    service_zone = 'Boro Zone'   as is_boro_zone

from {{ source('raw', 'taxi_zones') }}