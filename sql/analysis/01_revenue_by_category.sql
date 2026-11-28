SELECT
    p.category_name_english                AS category,
    count(*)                               AS items_sold,
    round(sum(f.item_total), 2)            AS revenue
FROM marts.fct_order_items f
JOIN marts.dim_products p USING (product_id)
WHERE f.order_status NOT IN ('canceled', 'unavailable')
GROUP BY p.category_name_english
ORDER BY revenue DESC
LIMIT 10;