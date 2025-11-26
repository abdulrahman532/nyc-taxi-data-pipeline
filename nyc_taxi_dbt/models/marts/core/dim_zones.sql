{{ config(materialized='table') }}

select
    location_id, borough, zone_name, service_zone, is_airport, is_yellow_zone, is_boro_zone, airport_code,
    case when is_airport then 'Airport' when borough = 'Manhattan' and is_yellow_zone then 'Manhattan Core' when borough = 'Manhattan' then 'Manhattan Other' else borough end as zone_category,
    zone_name like '%Financial%' as is_financial_district,
    zone_name like '%Midtown%' as is_midtown,
    zone_name like '%Times Sq%' or zone_name like '%Theatre%' as is_tourist_area
from {{ ref('stg_zones') }}
