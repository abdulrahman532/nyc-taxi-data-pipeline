{{ config(materialized='table') }}

with monthly as (
    select * from {{ ref('agg_monthly_overview') }}
)

select
    pickup_month,
    pickup_year,
    total_trips,
    total_revenue,
    congestion_revenue,
    round(congestion_revenue / nullif(total_revenue, 0) * 100, 2) as congestion_pct_of_revenue,
    cbd_fee_revenue,
    round(cbd_fee_revenue / nullif(total_revenue, 0) * 100, 2) as cbd_pct_of_revenue,
    airport_fee_revenue,
    fare_revenue,
    round(fare_revenue / nullif(total_revenue, 0) * 100, 2) as base_fare_pct,
    case 
        when pickup_month < '2019-02-01' then 'Pre-Congestion Surcharge'
        when pickup_month between '2019-02-01' and '2024-12-31' then 'Congestion Surcharge Era'
        else 'CBD Fee Era'
    end as fee_era
from monthly
order by pickup_month
