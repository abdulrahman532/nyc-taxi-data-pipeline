{{ config(materialized='table') }}

with monthly as (select * from {{ ref('agg_monthly') }}),
baseline_2019 as (select pickup_month_num, avg(total_trips) as baseline_trips from monthly where pickup_year = 2019 group by 1)
select
    m.pickup_month, m.pickup_year, m.pickup_month_num, m.total_trips, m.total_revenue,
    case when m.pickup_month < '2020-03-01' then 'Pre-COVID' when m.pickup_month between '2020-03-01' and '2020-06-30' then 'Lockdown' when m.pickup_month between '2020-07-01' and '2021-06-30' then 'Partial Recovery' else 'New Normal' end as covid_period,
    b.baseline_trips as same_month_2019_trips,
    round(m.total_trips * 100.0 / nullif(b.baseline_trips, 0), 1) as pct_of_2019,
    case when m.total_trips >= b.baseline_trips then 'Fully Recovered' when m.total_trips >= b.baseline_trips * 0.5 then 'Partial' else 'Struggling' end as recovery_status
from monthly m
left join baseline_2019 b on m.pickup_month_num = b.pickup_month_num
where m.pickup_year >= 2019
order by m.pickup_month
