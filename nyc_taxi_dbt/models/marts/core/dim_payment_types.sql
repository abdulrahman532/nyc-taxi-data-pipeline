{{ config(materialized='table') }}

select payment_type_id, payment_type_name, is_electronic, is_revenue_generating from (
    select 0 as payment_type_id, 'Flex Fare' as payment_type_name, true as is_electronic, true as is_revenue_generating union all
    select 1, 'Credit Card', true, true union all
    select 2, 'Cash', false, true union all
    select 3, 'No Charge', false, false union all
    select 4, 'Dispute', false, false union all
    select 5, 'Unknown', false, true union all
    select 6, 'Voided', false, false
)
