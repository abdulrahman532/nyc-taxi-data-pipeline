-- Generic test: ensures column has no negative values
{% test positive_value(model, column_name) %}
-- Usage in schema.yml:
--   tests:
--     - positive_value

select *
from {{ model }}
where {{ column_name }} < 0

{% endtest %}
