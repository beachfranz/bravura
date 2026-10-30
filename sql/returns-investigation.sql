-- Operational analysis only. No private product IDs, scenario labels or expected answers.
-- Fixed reporting cutoff; 60-day maturity window is a declared analytical choice.
WITH line_returns AS (
 SELECT order_line_id, sum(returned_quantity) returned_units,
        sum(refund_cents) refunds, sum(net_return_cost_cents) return_cost
 FROM bravura_demo.returns WHERE return_date <= DATE '2026-10-28' GROUP BY 1
)
SELECT p.product_id, p.product_name, date_trunc('quarter',l.order_date)::date purchase_quarter,
 count(*) sold_lines, count(r.order_line_id) returned_lines,
 count(r.order_line_id)::numeric / nullif(count(*),0) return_line_rate,
 sum(coalesce(r.returned_units,0))::numeric / nullif(sum(l.quantity),0) returned_unit_rate,
 sum(l.net_sales_cents)/100.0 sales_before_returns,
 sum(coalesce(r.refunds,0))/100.0 refunds,
 sum(l.gross_profit_cents)/100.0 gross_profit_before_returns,
 sum(l.contribution_cents-coalesce(r.return_cost,0))/100.0 contribution_after_returns
FROM bravura_demo.order_lines l
JOIN bravura_demo.products p USING(product_id)
JOIN bravura_demo.shipments s USING(order_id)
LEFT JOIN line_returns r USING(order_line_id)
WHERE s.actual_delivery_date <= DATE '2026-10-28' - 60
GROUP BY 1,2,3 ORDER BY returned_lines DESC;

-- All first returns, not just a selected product: compare equal 90-day windows.
-- 45-day offset is an analytical assumption. Association, not causal effect.
WITH first_return AS (
 SELECT l.customer_id, min(r.return_date) first_return
 FROM bravura_demo.returns r JOIN bravura_demo.order_lines l USING(order_line_id)
 WHERE r.return_date <= DATE '2026-10-28' GROUP BY 1
), windows AS (
 SELECT *, first_return+45 anchor FROM first_return
), coverage AS (
 SELECT min(order_date) first_sale,max(order_date) last_sale FROM bravura_demo.order_lines
)
SELECT w.customer_id,w.first_return,w.anchor-90 pre_start,w.anchor,w.anchor+90 post_end_exclusive,
 sum(CASE WHEN l.order_date < w.anchor THEN l.net_sales_cents ELSE 0 END)/100.0 pre_revenue,
 sum(CASE WHEN l.order_date >= w.anchor THEN l.net_sales_cents ELSE 0 END)/100.0 post_revenue
FROM windows w CROSS JOIN coverage c
JOIN bravura_demo.order_lines l ON l.customer_id=w.customer_id
 AND l.order_date>=w.anchor-90 AND l.order_date<w.anchor+90
WHERE w.anchor-90>=c.first_sale AND w.anchor+90<=c.last_sale
GROUP BY 1,2,3,4,5;
