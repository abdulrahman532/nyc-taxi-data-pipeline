{{ config(materialized='table') }}

-- Vendor dimension based on TLC data dictionary
-- https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

select vendor_id, vendor_name, vendor_code from (
    select 1 as vendor_id, 'Creative Mobile Technologies' as vendor_name, 'CMT' as vendor_code union all
    select 2, 'VeriFone Inc.', 'VFI' union all
    select 6, 'Myle Technologies', 'MYLE' union all
    select 7, 'Helix', 'HELIX'
)
