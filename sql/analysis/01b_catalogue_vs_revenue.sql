WITH catalogue AS (
    SELECT category_name_english AS category,
           count(*)               AS products
    FROM marts.dim_products
    GROUP BY 1
),
sales AS (
    SELECT p.category_name_english   AS category,
           count(*)                  AS items_sold,
           sum(f.item_total)         AS revenue
    FROM marts.fct_order_items f
    JOIN marts.dim_products p USING (product_id)
    WHERE f.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY 1
)
SELECT
    c.category,
    c.products,
    s.items_sold,
    round(s.revenue, 2)                    AS revenue,
    round(s.revenue / s.items_sold, 2)     AS revenue_per_item,
    rank() OVER (ORDER BY c.products DESC) AS rank_catalogue,
    rank() OVER (ORDER BY s.revenue DESC)  AS rank_revenue
FROM catalogue c
JOIN sales s USING (category)
ORDER BY rank_revenue
LIMIT 10;
/* Two CTEs, each answering one sub-question:
 catalogue (how many products per category)
sales (how much sold per category).
Then they're joined on the category. 
Both are grouped to one row per category before the join, 
so nothing is multiplied. It's the same rule as geolocation: 
make the key unique on both sides, then join.
revenue_per_item: revenue divided by items sold, 
which is the average price of a sale (freight included).
rank() OVER (ORDER BY ...): a window function, like ROW_NUMBER, but without PARTITION BY, so it ranks across the whole table. It gives each category its position in both rankings, side by side. */