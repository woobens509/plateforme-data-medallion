SELECT
    customer_id,
    customer_city AS ville,
    customer_state AS etat,
    'olist' AS source
FROM {{ ref('stg_olist_customers') }}

UNION

SELECT
    customer_id,
    city AS ville,
    state AS etat,
    'superstore' AS source
FROM {{ ref('stg_superstore') }}
GROUP BY customer_id, city, state