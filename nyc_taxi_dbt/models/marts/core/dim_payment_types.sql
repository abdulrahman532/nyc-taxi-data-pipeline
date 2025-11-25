{{ config(materialized='table') }}

select payment_type_id, payment_type_name from (
    select 0 as payment_type_id, 'Flex Fare' as payment_type_name union all
    select 1, 'Credit Card' union all
    select 2, 'Cash' union all
    select 3, 'No Charge' union all
    select 4, 'Dispute' union all
    select 5, 'Unknown' union all
    select 6, 'Voided'
)
