CREATE OR REPLACE VIEW staging.geolocation AS
SELECT
    lpad(trim(geolocation_zip_code_prefix), 5, '0')                       AS zip_prefix,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY geolocation_lat::numeric) AS lat,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY geolocation_lng::numeric) AS lng,
    mode() WITHIN GROUP (ORDER BY lower(unaccent(trim(geolocation_city)))) AS city,
    mode() WITHIN GROUP (ORDER BY upper(trim(geolocation_state)))         AS state,
    count(*)                                                               AS n_points
FROM raw.geolocation
GROUP BY lpad(trim(geolocation_zip_code_prefix), 5, '0');