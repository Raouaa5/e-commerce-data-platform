CREATE OR REPLACE VIEW staging.order_payments AS
SELECT 
order_id, 
payment_sequential::integer AS payment_sequential,
lower(trim(payment_type)) AS payment_type, 
payment_installments::integer AS payment_installements,
payment_value :: NUMERIC(10,2) AS payment_value FROM raw.order_payments;