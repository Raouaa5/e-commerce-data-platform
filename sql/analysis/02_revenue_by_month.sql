SELECT d.year_month AS mois ,count(DISTINCT f.order_id) AS orders,round(sum(f.item_total),2) as revenue 
FROM marts.fct_order_items f 
JOIN marts.dim_date d on d.date_day= f.purchase_date 
WHERE f.order_status NOT IN ('canceled', 'unavailable') 
GROUP BY d.year_month ORDER BY d.year_month;

SELECT f.purchase_date, count(DISTINCT f.order_id) AS orders
FROM marts.fct_order_items f
WHERE f.purchase_date BETWEEN '2017-11-17' AND '2017-11-30'
  AND f.order_status NOT IN ('canceled', 'unavailable')
GROUP BY 1 ORDER BY 2 DESC;