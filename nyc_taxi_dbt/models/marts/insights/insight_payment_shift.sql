{{ config(materialized='table') }}

select
    pickup_year, total_trips, credit_card_pct, cash_pct,
    lag(credit_card_pct) over (order by pickup_year) as prev_year_cc_pct,
    round(credit_card_pct - lag(credit_card_pct) over (order by pickup_year), 2) as cc_pct_change,
    case when credit_card_pct < 50 then 'Cash Dominant' when credit_card_pct between 50 and 70 then 'Transition' else 'Digital Dominant' end as payment_era
from {{ ref('agg_yearly') }}
order by pickup_year
