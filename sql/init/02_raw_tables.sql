-- =============================================================================
-- 02_raw_tables.sql
-- Raw-layer DDL — one table per source CSV file.
--
-- Design rules:
--   * Every column is TEXT: the raw layer accepts whatever the CSV contains,
--     no casting, no validation.  Type coercion happens in staging.
--   * Two metadata columns are appended to every table:
--       _loaded_at   – timestamp of the INSERT (set by the loader, not the DB)
--       _source_file – basename of the CSV that produced the row
--   * IF NOT EXISTS lets the script be re-run safely (idempotent).
--   * No constraints (no PK, no FK, no NOT NULL) – raw is a landing zone.
-- =============================================================================


-- ---------------------------------------------------------------------------
-- raw.orders
-- One row per order.
-- Clean key : order_id  (99,441 unique values, 0 duplicates confirmed).
-- Notable   : all timestamp columns arrive as plain text strings; convert
--             with TO_TIMESTAMP in staging.
--             160 orders have NULL order_approved_at (canceled/unavailable).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.orders (
    order_id                        TEXT,
    customer_id                     TEXT,
    order_status                    TEXT,
    order_purchase_timestamp        TEXT,
    order_approved_at               TEXT,
    order_delivered_carrier_date    TEXT,
    order_delivered_customer_date   TEXT,
    order_estimated_delivery_date   TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.customers
-- One row per (order, customer address).
-- Clean key : customer_id  (99,441 unique values, 0 duplicates confirmed).
-- Notable   : customer_id changes with every order for the same person.
--             customer_unique_id is the stable person identifier.
--             96,096 distinct customer_unique_id across 99,441 orders
--             → repeat rate 3.12 %.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id                     TEXT,
    customer_unique_id              TEXT,
    customer_zip_code_prefix        TEXT,
    customer_city                   TEXT,
    customer_state                  TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.order_items
-- One row per item line inside an order.
-- Clean key : (order_id, order_item_id)  (112,650 unique combos, 0 duplicates).
-- Notable   : price and freight_value arrive as numeric strings; cast to
--             NUMERIC in staging.
--             shipping_limit_date is a timestamp string.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.order_items (
    order_id                        TEXT,
    order_item_id                   TEXT,
    product_id                      TEXT,
    seller_id                       TEXT,
    shipping_limit_date             TEXT,
    price                           TEXT,
    freight_value                   TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.order_payments
-- One row per payment instrument used for an order.
-- Clean key : (order_id, payment_sequential)  (103,886 unique combos, 0 dupes).
-- Notable   : order_id alone is NOT unique (4,446 duplicates) — orders split
--             across credit card + N vouchers.
--             Max 29 payment rows for one order (voucher stacking, confirmed).
--             1 order has no payment row at all (status = created).
--             payment_value is a numeric string; cast in staging.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.order_payments (
    order_id                        TEXT,
    payment_sequential              TEXT,
    payment_type                    TEXT,
    payment_installments            TEXT,
    payment_value                   TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.order_reviews
-- One row per review submission (not per order — no clean key).
-- Neither review_id nor order_id is unique:
--   814 duplicate review_id values, 551 duplicate order_id values.
-- Staging rule: keep 1 review per order_id using the latest
--               review_answer_timestamp → 98,673 rows.
-- Notable   : review_comment_title    NULL in 88.3 % of rows (optional).
--             review_comment_message  NULL in 58.7 % of rows (optional).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.order_reviews (
    review_id                       TEXT,
    order_id                        TEXT,
    review_score                    TEXT,
    review_comment_title            TEXT,
    review_comment_message          TEXT,
    review_creation_date            TEXT,
    review_answer_timestamp         TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.products
-- One row per product.
-- Clean key : product_id  (32,951 unique values, 0 duplicates confirmed).
-- Notable   : 610 products have NULL in product_category_name AND
--             product_name_lenght AND product_description_lenght AND
--             product_photos_qty simultaneously — one coherent incomplete
--             block; flag with is_incomplete in staging, do not drop.
--             2 categories have no English translation:
--               pc_gamer
--               portateis_cozinha_e_preparadores_de_alimentos
--             Column names ship with typos from the source
--             (lenght instead of length) — keep as-is in raw, rename in staging.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.products (
    product_id                      TEXT,
    product_category_name           TEXT,
    product_name_lenght             TEXT,   -- source typo: kept intentionally
    product_description_lenght      TEXT,   -- source typo: kept intentionally
    product_photos_qty              TEXT,
    product_weight_g                TEXT,
    product_length_cm               TEXT,
    product_height_cm               TEXT,
    product_width_cm                TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.sellers
-- One row per seller.
-- Clean key : seller_id  (3,095 unique values, 0 duplicates confirmed).
-- Notable   : seller_zip_code_prefix joins to raw.geolocation for coordinates.
--             Join must go through the staged geolocation table (1 row per
--             prefix) to avoid the 151.7× fan-out of the raw point-cloud.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.sellers (
    seller_id                       TEXT,
    seller_zip_code_prefix          TEXT,
    seller_city                     TEXT,
    seller_state                    TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.geolocation
-- One row per GPS measurement inside a zip-code area.
-- No clean key: 1,000,163 raw rows for only 19,015 distinct zip prefixes
--   (median 29 rows/prefix, max 1,146).
-- NEVER join raw tables directly on geolocation_zip_code_prefix:
--   the fan-out is 151.7× — every customer row multiplies to ~52 rows.
-- Staging rule: aggregate to 1 row per prefix
--   (median lat/lng, mode city after lowercasing + accent-stripping,
--    mode state; handle the handful of prefixes that cross state lines).
-- Notable   : city names contain accent/case inconsistencies
--             (e.g. "sao paulo" vs "são paulo") — normalise in staging.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.geolocation (
    geolocation_zip_code_prefix     TEXT,
    geolocation_lat                 TEXT,
    geolocation_lng                 TEXT,
    geolocation_city                TEXT,
    geolocation_state               TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.product_category_name_translation
-- One row per product category name (Portuguese → English mapping).
-- Clean key : product_category_name  (71 unique values, 0 duplicates).
-- Notable   : 73 categories exist in raw.products but only 71 are in this
--             table — 2 are missing translations:
--               pc_gamer
--               portateis_cozinha_e_preparadores_de_alimentos
--             Add these two rows manually in staging with best-effort
--             translations ("pc_gamer" → "pc_gamer",
--             "portateis_cozinha_e_preparadores_de_alimentos"
--               → "portable_kitchen_food_preparers").
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.product_category_name_translation (
    product_category_name           TEXT,
    product_category_name_english   TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);



-- ---------------------------------------------------------------------------
-- raw.products
-- One row per product.
-- Clean key : product_id  (32,951 unique values, 0 duplicates confirmed).
-- Notable   : 610 products have NULL in product_category_name AND
--             product_name_lenght AND product_description_lenght AND
--             product_photos_qty simultaneously — one coherent incomplete
--             block; flag with is_incomplete in staging, do not drop.
--             2 categories have no English translation:
--               pc_gamer
--               portateis_cozinha_e_preparadores_de_alimentos
--             Column names ship with typos from the source
--             (lenght instead of length) — keep as-is in raw, rename in staging.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.products (
    product_id                      TEXT,
    product_category_name           TEXT,
    product_name_lenght             TEXT,   -- source typo: kept intentionally
    product_description_lenght      TEXT,   -- source typo: kept intentionally
    product_photos_qty              TEXT,
    product_weight_g                TEXT,
    product_length_cm               TEXT,
    product_height_cm               TEXT,
    product_width_cm                TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.sellers
-- One row per seller.
-- Clean key : seller_id  (3,095 unique values, 0 duplicates confirmed).
-- Notable   : seller_zip_code_prefix joins to raw.geolocation for coordinates.
--             Join must go through the staged geolocation table (1 row per
--             prefix) to avoid the 151.7× fan-out of the raw point-cloud.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.sellers (
    seller_id                       TEXT,
    seller_zip_code_prefix          TEXT,
    seller_city                     TEXT,
    seller_state                    TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.geolocation
-- One row per GPS measurement inside a zip-code area.
-- No clean key: 1,000,163 raw rows for only 19,015 distinct zip prefixes
--   (median 29 rows/prefix, max 1,146).
-- NEVER join raw tables directly on geolocation_zip_code_prefix:
--   the fan-out is 151.7× — every customer row multiplies to ~52 rows.
-- Staging rule: aggregate to 1 row per prefix
--   (median lat/lng, mode city after lowercasing + accent-stripping,
--    mode state; handle the handful of prefixes that cross state lines).
-- Notable   : city names contain accent/case inconsistencies
--             (e.g. "sao paulo" vs "são paulo") — normalise in staging.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.geolocation (
    geolocation_zip_code_prefix     TEXT,
    geolocation_lat                 TEXT,
    geolocation_lng                 TEXT,
    geolocation_city                TEXT,
    geolocation_state               TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);


-- ---------------------------------------------------------------------------
-- raw.product_category_name_translation
-- One row per product category name (Portuguese → English mapping).
-- Clean key : product_category_name  (71 unique values, 0 duplicates).
-- Notable   : 73 categories exist in raw.products but only 71 are in this
--             table — 2 are missing translations:
--               pc_gamer
--               portateis_cozinha_e_preparadores_de_alimentos
--             Add these two rows manually in staging with best-effort
--             translations ("pc_gamer" → "pc_gamer",
--             "portateis_cozinha_e_preparadores_de_alimentos"
--               → "portable_kitchen_food_preparers").
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.product_category_name_translation (
    product_category_name           TEXT,
    product_category_name_english   TEXT,
    _loaded_at                      TIMESTAMPTZ DEFAULT now(),
    _source_file                    TEXT
);