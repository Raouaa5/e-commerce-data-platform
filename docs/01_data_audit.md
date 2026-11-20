Files and grain

File	Rows	One row =	Key
orders	99,441	one order	order_id
customers	99,441	one customer per order	customer_id
order_items	112,650	one item in an order	order_id + order_item_id
order_payments	103,886	one payment of an order	order_id + payment_sequential
order_reviews	99,224	one review (messy)	no clean key
products	32,951	one product	product_id
sellers	3,095	one seller	seller_id
geolocation	1,000,163	one GPS point in a zip area	none
category translation	71	one category	product_category_name

Relationships: every item points to an existing order, product and seller; every order to an existing customer (all 0 orphans).

Things to remember

1. People vs orders: customer_unique_id is the person. 96,096 people, 99,441 orders, repeat rate 3.12 %.
2. Orders without items: 775 (603 unavailable, 164 canceled, 8 other).
3. Payments: key order_id + payment_sequential. 2,961 orders paid in several parts (max 29 vouchers). 1 delivered order has no payment.
4. Revenue: items + freight. Matches payments for 99.6 % of orders, 389 documented gaps.
5. Reviews: no clean key. Keep 1 review per order (latest answer) → 98,673 rows.
6. Geolocation: never join raw (151.7× fan-out). One row per prefix → 19,015 rows.
7. Products: 610 incomplete (flag). 2 categories untranslated (pc_gamer, portateis_cozinha_e_preparadores_de_alimentos).
8. Order dates: 160 never approved (14 of them delivered: anomaly). 2,965 never delivered to the customer.