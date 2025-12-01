{{ config(materialized='view', schema='insights') }}

with monthly as (select * from {{ ref('agg_monthly') }}),
baseline_2019 as (
    select date_trunc('month', pickup_month)::date as month_2019, avg(total_trips) as baseline_trips
    from monthly where pickup_year = 2019
    group by 1
)

select
    m.pickup_month,
    m.pickup_year,
    m.total_trips,
    b.baseline_trips,
    round(m.total_trips * 100.0 / nullif(b.baseline_trips, 0), 1) as pct_of_2019,
    case
        when m.total_trips >= b.baseline_trips then 'Fully Recovered'
        when m.total_trips >= b.baseline_trips * 0.7 then 'Strong Recovery'
        when m.total_trips >= b.baseline_trips * 0.5 then 'Partial Recovery'
        else 'Still Struggling'
    end as recovery_status
from monthly m
left join baseline_2019 b on date_trunc('month', m.pickup_month) = b.month_2019
where m.pickup_year >= 2019
order by m.pickup_month