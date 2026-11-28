DROP TABLE IF EXISTS marts.fct_order_items;

CREATE TABLE marts.fct_order_items AS
SELECT
order_id, 
i.order_item_id,
i.product_id,
i.price + i.freight_value AS item_total,
i.seller_id,
o.customer_id,
o.purchased_at::date AS  purchase_date,
o.order_status,
i.price,
i.freight_value FROM staging.order_items i
LEFT JOIN staging.orders o USING (order_id);

