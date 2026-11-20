CREATE OR REPLACE VIEW staging.orders AS
SELECT
    order_id,
    customer_id,
    lower(trim(order_status))                     AS order_status,
    order_purchase_timestamp::timestamp           AS purchased_at,
    order_approved_at::timestamp                  AS approved_at,
    order_delivered_carrier_date::timestamp       AS delivered_to_carrier_at,
    order_delivered_customer_date::timestamp      AS delivered_to_customer_at,
    order_estimated_delivery_date::date           AS estimated_delivery_date,
    (order_approved_at IS NULL
     AND order_status = 'delivered')              AS is_delivered_without_approval
FROM raw.orders;