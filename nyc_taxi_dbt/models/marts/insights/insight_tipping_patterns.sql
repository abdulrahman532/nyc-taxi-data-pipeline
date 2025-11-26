{{ config(materialized='table') }}

select
    pickup_zone, pickup_borough, pickup_zone_category,
    count(*) as total_trips,
    sum(case when payment_type_id = 1 then 1 else 0 end) as credit_card_trips,
    round(avg(case when payment_type_id = 1 then tip_amount end), 2) as avg_tip_amount,
    round(avg(case when payment_type_id = 1 then tip_percentage end), 2) as avg_tip_pct,
    case when avg(case when payment_type_id = 1 then tip_percentage end) >= 20 then 'Generous' when avg(case when payment_type_id = 1 then tip_percentage end) >= 15 then 'Standard' else 'Low' end as tip_tier,
    row_number() over (order by avg(case when payment_type_id = 1 then tip_percentage end) desc) as tip_rank
from {{ ref('obt_trips') }}
group by 1, 2, 3
having sum(case when payment_type_id = 1 then 1 else 0 end) >= 1000
order by avg_tip_pct desc
