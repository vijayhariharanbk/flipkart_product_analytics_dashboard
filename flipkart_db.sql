-- USE flipkart_db;

-- SELECT *
-- FROM seller_performance
-- LIMIT 10;

/************************************************************
flikpart_db Business Question Analysis:
************************************************************/
-- Q1. Find the total number of product listing and the average customer rating.
SELECT COUNT(*) AS total_num_of_products,
	ROUND(AVG(rating),2) AS avg_customer_rating
FROM category_catalog;

-- Q2. Find the minimum, maximum, and average retail price.
SELECT MIN(retail_price) AS min_price,
	MAX(retail_price) AS max_price,
	ROUND(AVG(retail_price), 2) AS avg_price
FROM category_catalog;

-- Q3. Find the minimum, maximum, and average calculated discount percentage.
SELECT MIN(discount_percentage) AS min_disc_pct,
	MAX(discount_percentage) AS max_disc_pct,
	ROUND(AVG(discount_percentage),2) AS avg_disc_pct
FROM category_catalog;

-- Q4. Find products with a calculated discount percentage greater than 30%.
SELECT product_name,
	discount_percentage
FROM category_catalog
WHERE discount_percentage > 30
ORDER BY discount_percentage DESC;

-- Q5. Find products with a customer rating of 4.0 or higher.
SELECT product_name,
	rating
FROM category_catalog
WHERE rating >= 4.0
ORDER BY rating DESC;

-- Q6. Find the number of product listings in each category and subcategory.
SELECT
    category,
    sub_category,
    COUNT(*) AS num_of_products
FROM category_catalog
GROUP BY category, sub_category
ORDER BY category, sub_category;

-- Q7. Find the average calculated discount percentage for each category.
SELECT
	category,
    ROUND(AVG(discount_percentage), 2) AS avg_discount
FROM category_catalog
GROUP BY category
ORDER BY avg_discount DESC;

-- Q8. Find categories having more than 100 product listings.
SELECT
	category,
    COUNT(*) AS product_listed
FROM category_catalog
GROUP BY category
HAVING COUNT(*) > 100;

-- Q9. Find brands having more than 10 product listings.
SELECT 
	brand,
    COUNT(*) AS product_listed
FROM category_catalog
GROUP BY brand
HAVING COUNT(*) > 10;

-- Q10. Find the top 10 products with the highest calculated discount percentage.
SELECT
	product_name,
    discount_percentage
FROM category_catalog
ORDER BY discount_percentage DESC
LIMIT 10;

-- Q11. Compare sellers by average product rating and total customer review count.
SELECT
	seller_name,
	COUNT(*) AS products_listed,
    ROUND(AVG(rating), 2) AS avg_product_rating,
    SUM(num_reviews) AS total_reviews
FROM seller_performance
GROUP BY seller_name
ORDER BY avg_product_rating DESC;

-- Q12. Find sellers whose listed products have more than 10,000 customer reviews in total
SELECT
	seller_name,
	COUNT(DISTINCT product_id) AS listed_products,
    SUM(num_reviews) AS total_customer_reviews
FROM seller_performance
GROUP BY seller_name
HAVING SUM(num_reviews) > 10000
ORDER BY total_customer_reviews DESC;

-- Q13. Find products whose discount price is higher than 
-- the average discount price using a subquery

SELECT
	product_name,
    discount_price
FROM category_catalog
WHERE discount_price >
	(SELECT
		AVG(discount_price)
	FROM category_catalog)
ORDER BY discount_price DESC;

-- Q14. Combine records from multiple product tables using UNION ALL, selecting
-- corresponding columns in the same order and using NULL for unavailable fields.
SELECT product_id, product_name, category, sub_category, brand,
       retail_price, discount_price, discount_percentage,
       rating, num_reviews, seller_name, stock_status,
       'flipkart_other_products' AS source_table
FROM flipkart_other_products

UNION ALL

SELECT product_id, product_name, category, sub_category, brand,
       retail_price, discount_price, discount_percentage,
       rating, num_reviews, NULL, NULL,
       'category_catalog'
FROM category_catalog

UNION ALL

SELECT product_id, product_name, NULL, NULL, NULL,
       NULL, NULL, NULL,
       rating, num_reviews, seller_name, stock_status,
       'seller_performance'
FROM seller_performance;

-- Q15. Create a seller-summary view and join it to product listings using
-- seller_name. Display the product name, product rating, review count,
-- stock status, seller's average product rating, and seller's total review count.

/***********************************
CREATING seller_summary VIEW
************************************/

CREATE OR REPLACE VIEW seller_summary AS
SELECT
	seller_name,
	COUNT(*) AS total_products,
    ROUND(AVG(rating), 2) AS seller_avg_rating,
    SUM(num_reviews) AS seller_total_reviews
FROM seller_performance
GROUP BY seller_name;

/***********************************
Joining the view with product listing
************************************/
SELECT
	p.product_name,
    p.rating AS product_rating,
	p.num_reviews AS review_count,
    p.stock_status,
    s.seller_avg_rating,
    s.seller_total_reviews
FROM flipkart_other_products p
JOIN seller_summary s
	ON p.seller_name = s.seller_name
ORDER BY p.product_id;



