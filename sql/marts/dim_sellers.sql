DROP TABLE IF EXISTS marts.dim_sellers;
CREATE TABLE marts.dim_sellers AS
SELECT
s.seller_id,
zip_prefix,
s.city,
s.state,
g.lat,
g.lng FROM staging.sellers s LEFT JOIN staging.geolocation g USING (zip_prefix);

