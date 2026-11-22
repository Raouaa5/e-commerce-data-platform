CREATE OR REPLACE VIEW staging.products AS
SELECT
    product_id,
    lower(trim(product_category_name))   AS category_name,
    product_name_lenght::integer         AS name_length,
    product_description_lenght::integer  AS description_length,
    product_photos_qty::integer          AS photos_qty,
    product_weight_g::integer            AS weight_g,
    product_length_cm::integer           AS length_cm,
    product_height_cm::integer           AS height_cm,
    product_width_cm::integer            AS width_cm,
    product_category_name IS NULL        AS is_incomplete
FROM raw.products;