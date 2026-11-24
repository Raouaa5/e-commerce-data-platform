DROP TABLE IF EXISTS marts.dim_products;

CREATE TABLE marts.dim_products AS
SELECT
    p.product_id,
    p.category_name,
    COALESCE(t.category_name_english, p.category_name, 'unknown') AS category_name_english,
    p.weight_g,
    p.length_cm,
    p.height_cm,
    p.width_cm,
    p.photos_qty,
    p.is_incomplete
FROM staging.products p
LEFT JOIN staging.category_translation t USING (category_name);