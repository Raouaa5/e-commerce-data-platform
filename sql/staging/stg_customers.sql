CREATE OR REPLACE VIEW staging.customers AS 
SELECT
customer_id,
customer_unique_id,
lpad(trim(customer_zip_code_prefix), 5, '0') AS zip_prefix,
upper(trim(customer_state)) AS state,
lower(trim(customer_city))  AS city FROM raw.customers;

