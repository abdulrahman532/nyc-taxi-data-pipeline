{{ config(materialized='view', schema='insights') }}

select
    pickup_month,
    pickup_year,
    total_revenue,
    congestion_revenue + airport_fee_revenue + cbd_fee_revenue as total_fees,
    round((congestion_revenue + airport_fee_revenue + cbd_fee_revenue) * 100.0 / nullif(total_revenue, 0), 2) as fees_pct_of_revenue,
    case
        when pickup_month < '2019-02-01' then 'No Extra Fees'
        when pickup_month < '2025-01-05' then 'Congestion Surcharge Only'
        else 'All Fees Active'
    end as fee_era
from {{ ref('agg_monthly') }}
order by pickup_month