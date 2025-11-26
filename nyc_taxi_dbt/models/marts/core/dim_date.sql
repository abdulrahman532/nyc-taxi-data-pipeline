{{ config(materialized='table') }}

-- DATE DIMENSION: Calendar table for time-based analysis
-- Covers full date range of taxi data: 2009-01-01 to 2030-12-31

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="'2009-01-01'",
        end_date="'2030-12-31'"
    ) }}
),

dates as (
    select
        date_day as date_id
    from date_spine
)

select
    date_id,
    
    -- Date parts
    year(date_id) as year,
    quarter(date_id) as quarter,
    month(date_id) as month,
    week(date_id) as week_of_year,
    day(date_id) as day_of_month,
    dayofweek(date_id) as day_of_week,
    dayofyear(date_id) as day_of_year,
    
    -- Date names
    dayname(date_id) as day_name,
    monthname(date_id) as month_name,
    
    -- Formatted dates
    date_trunc('month', date_id)::date as month_start,
    date_trunc('quarter', date_id)::date as quarter_start,
    date_trunc('year', date_id)::date as year_start,
    last_day(date_id) as month_end,
    
    -- Fiscal periods (assuming calendar year = fiscal year)
    year(date_id) as fiscal_year,
    quarter(date_id) as fiscal_quarter,
    
    -- Business day flags
    case when dayofweek(date_id) in (0, 6) then false else true end as is_weekday,
    case when dayofweek(date_id) in (0, 6) then true else false end as is_weekend,
    
    -- US Federal Holidays (simplified)
    case 
        when month(date_id) = 1 and day(date_id) = 1 then true  -- New Year's Day
        when month(date_id) = 7 and day(date_id) = 4 then true  -- Independence Day
        when month(date_id) = 12 and day(date_id) = 25 then true -- Christmas
        when month(date_id) = 11 and dayofweek(date_id) = 4 
             and day(date_id) between 22 and 28 then true -- Thanksgiving
        else false
    end as is_holiday,
    
    -- Special NYC events/periods
    case
        when month(date_id) = 12 and day(date_id) = 31 then 'New Years Eve'
        when month(date_id) = 3 and day(date_id) = 17 then 'St Patricks Day'
        when month(date_id) = 11 and dayofweek(date_id) = 4 
             and day(date_id) between 22 and 28 then 'Thanksgiving'
        when month(date_id) = 12 and day(date_id) between 20 and 31 then 'Holiday Season'
        else null
    end as special_event,
    
    -- COVID periods
    case
        when date_id between '2020-03-15' and '2020-06-07' then 'Lockdown'
        when date_id between '2020-06-08' and '2020-12-31' then 'Reopening Phase 1-4'
        when date_id between '2021-01-01' and '2021-06-30' then 'Vaccine Rollout'
        when date_id >= '2021-07-01' then 'Post-Pandemic'
        else 'Pre-Pandemic'
    end as covid_period,
    
    -- Congestion pricing period (started Jan 2025)
    date_id >= '2025-01-05' as is_congestion_pricing_active

from dates
