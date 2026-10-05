WITH dates AS (
    SELECT DISTINCT order_purchase_timestamp::date AS date_value
    FROM {{ ref('stg_olist_orders') }}
    WHERE order_purchase_timestamp IS NOT NULL

    UNION

    SELECT DISTINCT order_date AS date_value
    FROM {{ ref('stg_superstore') }}
    WHERE order_date IS NOT NULL
)

SELECT
    date_value,
    EXTRACT(YEAR FROM date_value) AS annee,
    EXTRACT(MONTH FROM date_value) AS mois,
    EXTRACT(DAY FROM date_value) AS jour,
    TO_CHAR(date_value, 'Month') AS nom_mois,
    EXTRACT(DOW FROM date_value) AS jour_semaine
FROM dates