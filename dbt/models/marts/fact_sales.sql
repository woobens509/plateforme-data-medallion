SELECT
    oi.order_id,
    oi.product_id,
    o.customer_id,
    o.order_purchase_timestamp::date AS date_vente,
    oi.price AS montant_vente,
    oi.freight_value AS frais_port,
    1 AS quantite,
    'olist' AS source
FROM {{ ref('stg_olist_order_items') }} oi
JOIN {{ ref('stg_olist_orders') }} o ON oi.order_id = o.order_id

UNION ALL

SELECT
    order_id,
    product_id,
    customer_id,
    order_date AS date_vente,
    sales AS montant_vente,
    0 AS frais_port,
    quantity AS quantite,
    'superstore' AS source
FROM {{ ref('stg_superstore') }}