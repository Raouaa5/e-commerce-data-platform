DROP TABLE IF EXISTS marts.fct_orders;

CREATE TABLE marts.fct_orders AS
WITH items AS (
    SELECT
        order_id,
        count(*)                       AS item_count,
        sum(price)                     AS items_price,
        sum(freight_value)             AS items_freight,
        sum(price + freight_value)     AS order_revenue
    FROM staging.order_items
    GROUP BY order_id
),
payments AS (
    SELECT
        order_id,
        count(*)                       AS payment_count,
        sum(payment_value)             AS payment_total
    FROM staging.order_payments
    GROUP BY order_id
)
SELECT
    -- keys
    o.order_id,
    o.customer_id,
    o.purchased_at::date               AS purchase_date,
    -- status
    o.order_status,
    -- dates
    o.purchased_at,
    o.approved_at,
    o.delivered_to_carrier_at,
    o.delivered_to_customer_at,
    o.estimated_delivery_date,
    -- measures from items and payments
    COALESCE(i.item_count, 0)          AS item_count,
    COALESCE(i.order_revenue, 0)       AS order_revenue,
    p.payment_total,
    -- review
    r.review_score
FROM staging.orders o
LEFT JOIN items    i USING (order_id)
LEFT JOIN payments p USING (order_id)
LEFT JOIN staging.order_reviews r USING (order_id);