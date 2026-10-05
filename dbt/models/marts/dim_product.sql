SELECT
    product_id,
    category AS categorie,
    sub_category AS sous_categorie,
    product_name AS nom_produit,
    'superstore' AS source
FROM {{ ref('stg_superstore') }}
GROUP BY product_id, category, sub_category, product_name

UNION

SELECT
    product_id,
    NULL AS categorie,
    NULL AS sous_categorie,
    NULL AS nom_produit,
    'olist' AS source
FROM {{ ref('stg_olist_order_items') }}
GROUP BY product_id