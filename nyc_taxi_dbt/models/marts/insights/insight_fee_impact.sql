{{ config(materialized='table') }}

select
    pickup_month, pickup_year, total_trips, total_revenue,
    congestion_revenue, airport_fee_revenue, cbd_fee_revenue,
    round(congestion_revenue * 100.0 / nullif(total_revenue, 0), 2) as congestion_pct,
    round(airport_fee_revenue * 100.0 / nullif(total_revenue, 0), 2) as airport_fee_pct,
    round(cbd_fee_revenue * 100.0 / nullif(total_revenue, 0), 2) as cbd_pct,
    congestion_revenue + airport_fee_revenue + cbd_fee_revenue as total_fees,
    case when pickup_month < '2019-02-01' then 'No Fees' when pickup_month < '2025-01-05' then 'Congestion Era' else 'All Fees' end as fee_era
from {{ ref('agg_monthly') }}
order by pickup_month
