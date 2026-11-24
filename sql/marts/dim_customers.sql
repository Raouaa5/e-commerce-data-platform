DROP TABLE IF EXISTS marts.dim_customers;

CREATE TABLE marts.dim_customers AS
SELECT
    c.customer_id,
    c.customer_unique_id,
    zip_prefix,
    c.city,
    c.state,
    g.lat,
    g.lng
FROM staging.customers c
LEFT JOIN staging.geolocation g USING (zip_prefix);