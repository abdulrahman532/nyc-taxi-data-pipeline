{{ config(materialized='view', schema='insights') }}

select
    pickup_zone,
    pickup_borough,
    count(*) as total_trips,
    sum(case when payment_type_id = 1 then 1 else 0 end) as credit_card_trips,
    round(avg(tip_amount) filter (where payment_type_id = 1), 2) as avg_tip_amount,
    round(avg(tip_percentage) filter (where payment_type_id = 1), 2) as avg_tip_pct,
    case
        when avg(tip_percentage) filter (where payment_type_id = 1) >= 20 then 'Generous'
        when avg(tip_percentage) filter (where payment_type_id = 1) >= 15 then 'Standard'
        else 'Stingy'
    end as tip_tier,
    row_number() over (order by avg(tip_percentage) filter (where payment_type_id = 1) desc) as tip_rank
from {{ ref('obt_trips') }}
group by pickup_zone, pickup_borough
having sum(case when payment_type_id = 1 then 1 else 0 end) >= 1000
order by avg_tip_pct desc