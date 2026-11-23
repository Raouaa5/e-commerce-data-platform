CREATE OR REPLACE VIEW staging.category_translation AS
SELECT
    lower(trim(product_category_name))         AS category_name,
    lower(trim(product_category_name_english)) AS category_name_english
FROM raw.product_category_name_translation;