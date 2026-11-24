DROP TABLE IF EXISTS marts.dim_date;

CREATE TABLE marts.dim_date AS
SELECT
    d::date                             AS date_day,
    extract(year    FROM d)::integer    AS year,
    extract(quarter FROM d)::integer    AS quarter,
    extract(month   FROM d)::integer    AS month,
    to_char(d, 'YYYY-MM')               AS year_month,
    to_char(d, 'TMMonth')               AS month_name,
    extract(isodow  FROM d)::integer    AS day_of_week,
    to_char(d, 'TMDay')                 AS day_name,
    extract(isodow FROM d) IN (6, 7)    AS is_weekend
FROM generate_series('2016-01-01'::date, '2018-12-31'::date, interval '1 day') AS d;