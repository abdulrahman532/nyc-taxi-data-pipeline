{{ config(materialized='table') }}

select rate_code_id, rate_code_name from (
    select 1 as rate_code_id, 'Standard Rate' as rate_code_name union all
    select 2, 'JFK' union all
    select 3, 'Newark' union all
    select 4, 'Nassau/Westchester' union all
    select 5, 'Negotiated Fare' union all
    select 6, 'Group Ride' union all
    select 99, 'Unknown'
)
