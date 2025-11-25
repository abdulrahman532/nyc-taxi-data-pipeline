{{ config(materialized='table') }}

select vendor_id, vendor_name from (
    select 1 as vendor_id, 'Creative Mobile Technologies' as vendor_name union all
    select 2, 'Curb Mobility' union all
    select 6, 'Myle Technologies' union all
    select 7, 'Helix'
)
