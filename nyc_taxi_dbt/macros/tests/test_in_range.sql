{% test in_range(model, column_name, min_value, max_value) %}
-- Generic test: ensures column value is between min and max
-- Usage in schema.yml:
--   tests:
--     - in_range:
--         min_value: 0
--         max_value: 9

select *
from {{ model }}
where {{ column_name }} < {{ min_value }}
   or {{ column_name }} > {{ max_value }}

{% endtest %}
