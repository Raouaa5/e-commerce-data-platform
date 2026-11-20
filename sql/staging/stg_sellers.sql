CREATE OR REPLACE VIEW staging.sellers AS 
SELECT
seller_id,
lpad(trim(seller_zip_code_prefix), 5, '0') AS zip_prefix,
lower(trim(seller_city)) AS city,
upper(trim(seller_state)) AS state From raw.sellers;