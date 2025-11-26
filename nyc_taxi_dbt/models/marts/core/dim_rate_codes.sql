{{ config(materialized='table') }}

select rate_code_id, rate_code_name, is_airport_rate, is_flat_rate from (
    select 1 as rate_code_id, 'Standard' as rate_code_name, false as is_airport_rate, false as is_flat_rate union all
    select 2, 'JFK', true, true union all
    select 3, 'Newark', true, true union all
    select 4, 'Nassau/Westchester', false, false union all
    select 5, 'Negotiated', false, true union all
    select 6, 'Group Ride', false, false union all
    select 99, 'Unknown', false, false
)
