"""
Flipkart Product Analytics - Streamlit Dashboard
Run with:  streamlit run app.py
"""

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from streamlit_option_menu import option_menu


# ============================================================
# 1. DATABASE SETTINGS  (change the password to your own)
# ============================================================
DB_USER = "USER_NAME"
DB_PASSWORD = "YOUR_PASSWORD"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "flipkart_db"

DB_URL = os.getenv(
    "FLIPKART_DB_URL",
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

st.set_page_config(page_title="Flipkart Product Analytics", page_icon="🛒", layout="wide")


@st.cache_resource
def get_engine():
    """Create the database connection once and reuse it."""
    return create_engine(DB_URL)


engine = get_engine()


# ============================================================
# 2. LOADING DATA FROM MYSQL
# ============================================================
@st.cache_data
def load_products():
    """All priced products: flipkart_other_products + category_catalog."""
    query = """
        SELECT product_id, product_name, category, sub_category, brand,
               retail_price, discount_price, discount_percentage, discount_amount,
               rating, num_reviews, rating_category, discount_range,
               seller_name, stock_status, 'Products table' AS source
        FROM flipkart_other_products

        UNION ALL

        SELECT product_id, product_name, category, sub_category, brand,
               retail_price, discount_price, discount_percentage, discount_amount,
               rating, num_reviews, rating_category, discount_range,
               NULL, NULL, 'Catalog table'
        FROM category_catalog
    """
    return pd.read_sql(text(query), engine)


@st.cache_data
def load_sellers():
    return pd.read_sql(text("SELECT * FROM seller_performance"), engine)


def run_query(query, params=None):
    """Run a SELECT query and return the result as a DataFrame."""
    return pd.read_sql(text(query), engine, params=params)


def run_change(query, params):
    """Run an INSERT / UPDATE / DELETE query, then refresh the cached data."""
    with engine.begin() as conn:
        result = conn.execute(text(query), params)
    st.cache_data.clear()
    return result.rowcount


# ============================================================
# 3. HELPER FUNCTIONS (same rules as the cleaning notebook)
# ============================================================
CATEGORY_SUBCATEGORIES = {
    "Electronics": ["Audio", "Laptops", "Mobiles", "Televisions", "Wearables"],
    "Fashion": ["Apparel", "Footwear"],
    "Sports": ["Cricket", "Football"],
}
STOCK_OPTIONS = ["In Stock", "Limited Stock", "Out of Stock"]


def get_rating_category(rating):
    if rating >= 4.5:
        return "Excellent"
    elif rating >= 4.0:
        return "Good"
    else:
        return "Average"


def get_discount_range(pct):
    if pct <= 20:
        return "0-20%"
    elif pct <= 40:
        return "21-40%"
    elif pct <= 60:
        return "41-60%"
    elif pct <= 80:
        return "61-80%"
    else:
        return "81-100%"


def calculate_prices(retail_price, discount_percentage):
    """Work out discount price and discount amount from retail price and discount %."""
    discount_price = round(retail_price * (1 - discount_percentage / 100), 2)
    discount_amount = round(retail_price - discount_price, 2)
    return discount_price, discount_amount


def rupees(value):
    return f"₹{value:,.0f}"


# ============================================================
# 4. SIDEBAR: MENU + FILTERS
# ============================================================
with st.sidebar:
    page = option_menu(
        "Flipkart Analytics",
        ["Dashboard", "Data Explorer", "Analysis", "SQL Query Explorer", "CRUD Operations"],
        icons=["speedometer2", "table", "bar-chart", "code-square", "pencil-square"],
        menu_icon="cart",
        default_index=0,
    )

products = load_products()
sellers = load_sellers()


def sidebar_filters(df):
    """Show the filters in the sidebar and return the filtered DataFrame."""
    st.sidebar.markdown("### Filters")

    categories = st.sidebar.multiselect("Category", sorted(df["category"].unique()))
    if categories:
        df = df[df["category"].isin(categories)]

    sub_categories = st.sidebar.multiselect("Sub-category", sorted(df["sub_category"].unique()))
    if sub_categories:
        df = df[df["sub_category"].isin(sub_categories)]

    brands = st.sidebar.multiselect("Brand", sorted(df["brand"].unique()))
    if brands:
        df = df[df["brand"].isin(brands)]

    seller_list = sorted(df["seller_name"].dropna().unique())
    chosen_sellers = st.sidebar.multiselect("Seller", seller_list,
                                            help="Only the products table has sellers")
    if chosen_sellers:
        df = df[df["seller_name"].isin(chosen_sellers)]

    stock = st.sidebar.multiselect("Stock status", STOCK_OPTIONS,
                                   help="Only the products table has stock status")
    if stock:
        df = df[df["stock_status"].isin(stock)]

    min_rating, max_rating = st.sidebar.slider("Rating", 0.0, 5.0, (0.0, 5.0), step=0.1)
    df = df[df["rating"].between(min_rating, max_rating)]

    min_price, max_price = st.sidebar.slider("Retail price (₹)", 0, 150000, (0, 150000), step=1000)
    df = df[df["retail_price"].between(min_price, max_price)]

    min_disc, max_disc = st.sidebar.slider("Discount %", 0, 100, (0, 100))
    df = df[df["discount_percentage"].between(min_disc, max_disc)]

    st.sidebar.caption(f"{len(df):,} products match the filters")
    return df


# ============================================================
# 5. PAGE: DASHBOARD
# ============================================================
def show_dashboard(df):
    st.title("🛒 Flipkart Product Analytics Dashboard")

    if df.empty:
        st.warning("No products match the selected filters.")
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Products", f"{len(df):,}")
    col2.metric("Avg Rating", f"{df['rating'].mean():.2f}")
    col3.metric("Avg Discount %", f"{df['discount_percentage'].mean():.2f}%")
    col4.metric("Avg Retail Price", rupees(df["retail_price"].mean()))
    col5.metric("Out of Stock", f"{(df['stock_status'] == 'Out of Stock').sum():,}")

    left, right = st.columns(2)

    with left:
        category_counts = df.groupby(["category", "sub_category"]).size().reset_index(name="products")
        fig = px.bar(category_counts, x="products", y="category", color="sub_category",
                     orientation="h", title="Products by Category & Sub-category")
        st.plotly_chart(fig)

    with right:
        stock_counts = df["stock_status"].value_counts().reset_index()
        stock_counts.columns = ["stock_status", "products"]
        fig = px.pie(stock_counts, names="stock_status", values="products", hole=0.5,
                     title="Stock Status (products table only)")
        st.plotly_chart(fig)

    left, right = st.columns(2)

    with left:
        rating_counts = df["rating_category"].value_counts().reset_index()
        rating_counts.columns = ["rating_category", "products"]
        fig = px.pie(rating_counts, names="rating_category", values="products", hole=0.5,
                     title="Products by Rating Category")
        st.plotly_chart(fig)

    with right:
        range_counts = df["discount_range"].value_counts().sort_index().reset_index()
        range_counts.columns = ["discount_range", "products"]
        fig = px.bar(range_counts, x="discount_range", y="products", text="products",
                     title="Products by Discount Range")
        st.plotly_chart(fig)


# ============================================================
# 6. PAGE: DATA EXPLORER
# ============================================================
def show_data_explorer(df):
    st.title("🔎 Data Explorer")
    st.write("Use the filters in the sidebar, or search by product name below.")

    search = st.text_input("Search product name", key="explorer_search")
    if search:
        df = df[df["product_name"].str.contains(search, case=False)]

    st.write(f"Showing **{len(df):,}** products")
    st.dataframe(df, hide_index=True)

    st.download_button(
        "⬇️ Download filtered data as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="flipkart_filtered_products.csv",
        mime="text/csv",
    )


# ============================================================
# 7. PAGE: ANALYSIS (product, category, brand, pricing, discount, seller)
# ============================================================
def show_analysis(df, seller_df):
    st.title("📊 Business Analysis")

    if df.empty:
        st.warning("No products match the selected filters.")
        return

    tabs = st.tabs(["Product", "Category", "Brand", "Pricing", "Discount", "Seller"])

    # ---- Product ----
    with tabs[0]:
        st.subheader("Top 10 products by number of reviews")
        top_reviews = df.sort_values("num_reviews", ascending=False).head(10)
        st.dataframe(top_reviews[["product_name", "category", "rating", "num_reviews"]], hide_index=True)

        st.subheader("Top 10 rated products (most reviewed first)")
        top_rated = df.sort_values(["rating", "num_reviews"], ascending=False).head(10)
        st.dataframe(top_rated[["product_name", "category", "rating", "num_reviews"]], hide_index=True)

    # ---- Category ----
    with tabs[1]:
        category_summary = df.groupby("category").agg(
            products=("product_id", "count"),
            avg_rating=("rating", "mean"),
            avg_discount=("discount_percentage", "mean"),
        ).round(2).reset_index()
        st.dataframe(category_summary, hide_index=True)

        fig = px.bar(category_summary, x="category", y="products", text="products",
                     title="Products by Category")
        st.plotly_chart(fig)

    # ---- Brand ----
    with tabs[2]:
        brand_summary = df.groupby("brand").agg(
            products=("product_id", "count"),
            avg_rating=("rating", "mean"),
            avg_discount=("discount_percentage", "mean"),
        ).round(2).sort_values("products", ascending=False).reset_index()

        fig = px.bar(brand_summary, x="brand", y="products", text="products",
                     title="Products by Brand")
        st.plotly_chart(fig)
        st.dataframe(brand_summary, hide_index=True)

    # ---- Pricing ----
    with tabs[3]:
        price_summary = df.groupby("category")[["retail_price", "discount_price"]].mean().round(0).reset_index()
        price_long = price_summary.melt(id_vars="category", var_name="price_type", value_name="average_price")
        fig = px.bar(price_long, x="category", y="average_price", color="price_type", barmode="group",
                     title="Average Retail vs Discount Price by Category (₹)")
        st.plotly_chart(fig)

        fig = px.histogram(df, x="retail_price", nbins=30, title="Retail Price Distribution (₹)")
        st.plotly_chart(fig)

    # ---- Discount ----
    with tabs[4]:
        discount_by_category = df.groupby("category")["discount_percentage"].mean().round(2).reset_index()
        fig = px.bar(discount_by_category, x="category", y="discount_percentage", text="discount_percentage",
                     title="Average Discount % by Category")
        st.plotly_chart(fig)

        st.subheader("Top 10 products by discount amount")
        top_discount = df.sort_values("discount_amount", ascending=False).head(10)
        st.dataframe(top_discount[["product_name", "category", "retail_price",
                                   "discount_percentage", "discount_amount"]], hide_index=True)

    # ---- Seller ----
    with tabs[5]:
        st.caption("Listings, ratings and stock come from the seller_performance table. "
                   "Discounts come from the products table.")

        seller_summary = seller_df.groupby("seller_name").agg(
            products=("product_id", "count"),
            avg_rating=("rating", "mean"),
            total_reviews=("num_reviews", "sum"),
        ).round(2).sort_values("products", ascending=False).reset_index()

        seller_discount = (products.dropna(subset=["seller_name"])
                           .groupby("seller_name")["discount_percentage"].mean().round(2)
                           .reset_index(name="avg_discount"))
        seller_summary = seller_summary.merge(seller_discount, on="seller_name", how="left")
        st.dataframe(seller_summary, hide_index=True)

        fig = px.bar(seller_summary, x="seller_name", y="products", text="products",
                     title="Product Listings by Seller")
        st.plotly_chart(fig)

        stock_by_seller = seller_df.groupby(["seller_name", "stock_status"]).size().reset_index(name="products")
        fig = px.histogram(stock_by_seller, x="seller_name", y="products", color="stock_status",
                           barnorm="percent", title="Stock Status by Seller (%)")
        st.plotly_chart(fig)


# ============================================================
# 8. PAGE: SQL QUERY EXPLORER
# ============================================================
SQL_QUERIES = {
    "Q1. Total product listings and average rating": """
SELECT COUNT(*) AS total_products,
       ROUND(AVG(rating), 2) AS avg_customer_rating
FROM category_catalog""",

    "Q2. Minimum, maximum and average retail price": """
SELECT MIN(retail_price) AS min_price,
       MAX(retail_price) AS max_price,
       ROUND(AVG(retail_price), 2) AS avg_price
FROM category_catalog""",

    "Q3. Minimum, maximum and average discount percentage": """
SELECT MIN(discount_percentage) AS min_disc_pct,
       MAX(discount_percentage) AS max_disc_pct,
       ROUND(AVG(discount_percentage), 2) AS avg_disc_pct
FROM category_catalog""",

    "Q4. Products with discount greater than 30%": """
SELECT product_name, discount_percentage
FROM category_catalog
WHERE discount_percentage > 30
ORDER BY discount_percentage DESC""",

    "Q5. Products rated 4.0 or higher": """
SELECT product_name, rating
FROM category_catalog
WHERE rating >= 4.0
ORDER BY rating DESC""",

    "Q6. Product listings by category and sub-category": """
SELECT category, sub_category, COUNT(*) AS num_of_products
FROM category_catalog
GROUP BY category, sub_category
ORDER BY category, sub_category""",

    "Q7. Average discount percentage by category": """
SELECT category, ROUND(AVG(discount_percentage), 2) AS avg_discount
FROM category_catalog
GROUP BY category
ORDER BY avg_discount DESC""",

    "Q8. Categories with more than 100 listings": """
SELECT category, COUNT(*) AS product_listed
FROM category_catalog
GROUP BY category
HAVING COUNT(*) > 100""",

    "Q9. Brands with more than 10 listings": """
SELECT brand, COUNT(*) AS product_listed
FROM category_catalog
GROUP BY brand
HAVING COUNT(*) > 10""",

    "Q10. Top 10 products by discount percentage": """
SELECT product_name, discount_percentage
FROM category_catalog
ORDER BY discount_percentage DESC
LIMIT 10""",

    "Q11. Sellers by average rating and total reviews": """
SELECT seller_name,
       COUNT(*) AS products_listed,
       ROUND(AVG(rating), 2) AS avg_product_rating,
       SUM(num_reviews) AS total_reviews
FROM seller_performance
GROUP BY seller_name
ORDER BY avg_product_rating DESC""",

    "Q12. Sellers with more than 10,000 reviews in total": """
SELECT seller_name,
       COUNT(DISTINCT product_id) AS listed_products,
       SUM(num_reviews) AS total_customer_reviews
FROM seller_performance
GROUP BY seller_name
HAVING SUM(num_reviews) > 10000
ORDER BY total_customer_reviews DESC""",

    "Q13. Products priced above the average discount price (subquery)": """
SELECT product_name, discount_price
FROM category_catalog
WHERE discount_price > (SELECT AVG(discount_price) FROM category_catalog)
ORDER BY discount_price DESC""",

    "Q14. All product tables combined (UNION ALL)": """
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
FROM seller_performance""",

    "Q15. Products with their seller summary (JOIN)": """
SELECT p.product_name,
       p.rating       AS product_rating,
       p.num_reviews  AS review_count,
       p.stock_status,
       s.seller_avg_rating,
       s.seller_total_reviews
FROM flipkart_other_products p
JOIN (
    SELECT seller_name,
           ROUND(AVG(rating), 2) AS seller_avg_rating,
           SUM(num_reviews)      AS seller_total_reviews
    FROM seller_performance
    GROUP BY seller_name
) s ON p.seller_name = s.seller_name
ORDER BY p.product_id""",

    "Q16. Sellers with the highest average discounts": """
SELECT seller_name,
       COUNT(*) AS products,
       ROUND(AVG(discount_percentage), 2) AS avg_discount
FROM flipkart_other_products
GROUP BY seller_name
ORDER BY avg_discount DESC""",

    "Q17. Stock status by seller": """
SELECT seller_name, stock_status, COUNT(*) AS products
FROM seller_performance
GROUP BY seller_name, stock_status
ORDER BY seller_name, stock_status""",

    "Q18. Categories by rating and discount": """
SELECT category,
       ROUND(AVG(rating), 2) AS avg_rating,
       ROUND(AVG(discount_percentage), 2) AS avg_discount
FROM category_catalog
GROUP BY category
ORDER BY avg_rating DESC, avg_discount DESC""",

    "Q19. Priority products (rating 4.5+, discount 40%+, above-average reviews)": """
SELECT product_name, rating, discount_percentage, num_reviews
FROM category_catalog
WHERE rating >= 4.5
  AND discount_percentage >= 40
  AND num_reviews > (SELECT AVG(num_reviews) FROM category_catalog)
ORDER BY rating DESC, discount_percentage DESC, num_reviews DESC
LIMIT 10""",
}


def show_sql_explorer():
    st.title("🧮 SQL Query Explorer")
    st.write("Pick a business question to see its SQL query and the result from MySQL.")

    question = st.selectbox("Business question", list(SQL_QUERIES.keys()), key="sql_question")
    query = SQL_QUERIES[question]

    st.code(query.strip(), language="sql")

    result = run_query(query)
    st.write(f"**{len(result):,} rows returned**")
    st.dataframe(result, hide_index=True)


# ============================================================
# 9. PAGE: CRUD OPERATIONS (on the flipkart_other_products table)
# ============================================================
def show_crud():
    st.title("✏️ CRUD Operations")
    st.write("Create, read, update and delete product records in the **flipkart_other_products** table.")

    create_tab, read_tab, update_tab, delete_tab = st.tabs(["➕ Create", "📖 Read", "🔄 Update", "🗑️ Delete"])

    brands = sorted(products["brand"].unique())
    seller_names = sorted(sellers["seller_name"].unique())

    # ---------------- CREATE ----------------
    with create_tab:
        st.subheader("Add a new product")

        next_id = int(run_query("SELECT MAX(product_id) AS max_id FROM flipkart_other_products")["max_id"][0]) + 1

        col1, col2 = st.columns(2)
        with col1:
            new_id = st.number_input("Product ID", min_value=1, value=next_id, step=1, key="c_id")
            new_name = st.text_input("Product name", key="c_name")
            new_category = st.selectbox("Category", list(CATEGORY_SUBCATEGORIES.keys()), key="c_cat")
            new_sub = st.selectbox("Sub-category", CATEGORY_SUBCATEGORIES[new_category], key="c_sub")
            new_brand = st.selectbox("Brand", brands, key="c_brand")
            new_seller = st.selectbox("Seller", seller_names, key="c_seller")
        with col2:
            new_retail = st.number_input("Retail price (₹)", min_value=1.0, value=1000.0, step=100.0, key="c_retail")
            new_pct = st.number_input("Discount %", min_value=0.0, max_value=100.0, value=10.0, step=0.5, key="c_pct")
            new_rating = st.number_input("Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1, key="c_rating")
            new_reviews = st.number_input("Number of reviews", min_value=0, value=0, step=1, key="c_reviews")
            new_stock = st.selectbox("Stock status", STOCK_OPTIONS, key="c_stock")

        discount_price, discount_amount = calculate_prices(new_retail, new_pct)
        st.info(f"Discount price: {rupees(discount_price)}  |  Discount amount: {rupees(discount_amount)}  |  "
                f"Rating category: {get_rating_category(new_rating)}  |  Discount range: {get_discount_range(new_pct)}")

        if st.button("Add product", type="primary", key="c_button"):
            if new_name.strip() == "":
                st.error("Please enter a product name.")
            else:
                try:
                    run_change("""
                        INSERT INTO flipkart_other_products
                        (product_id, product_name, category, sub_category, brand,
                         retail_price, discount_price, discount_percentage, discount_amount, price_difference,
                         rating, num_reviews, seller_name, stock_status, rating_category, discount_range, rating_filled)
                        VALUES
                        (:id, :name, :category, :sub, :brand,
                         :retail, :dprice, :pct, :damount, :damount,
                         :rating, :reviews, :seller, :stock, :rcat, :drange, :filled)
                    """, {
                        "id": int(new_id), "name": new_name.strip(), "category": new_category, "sub": new_sub,
                        "brand": new_brand, "retail": new_retail, "dprice": discount_price, "pct": new_pct,
                        "damount": discount_amount, "rating": new_rating, "reviews": int(new_reviews),
                        "seller": new_seller, "stock": new_stock, "rcat": get_rating_category(new_rating),
                        "drange": get_discount_range(new_pct), "filled": False,
                    })
                    st.success(f"Product {int(new_id)} added.")
                except IntegrityError:
                    st.error(f"Product ID {int(new_id)} already exists. Use a different ID.")

    # ---------------- READ ----------------
    with read_tab:
        st.subheader("Find products")
        search_by = st.radio("Search by", ["Product ID", "Product name"], horizontal=True, key="r_by")

        if search_by == "Product ID":
            pid = st.number_input("Product ID", min_value=1, value=66667, step=1, key="r_id")
            result = run_query("SELECT * FROM flipkart_other_products WHERE product_id = :id", {"id": int(pid)})
        else:
            name = st.text_input("Product name contains", key="r_name")
            result = run_query("SELECT * FROM flipkart_other_products WHERE product_name LIKE :name LIMIT 100",
                               {"name": f"%{name}%"})

        if result.empty:
            st.warning("No matching product found.")
        else:
            st.dataframe(result, hide_index=True)

    # ---------------- UPDATE ----------------
    with update_tab:
        st.subheader("Update a product")
        pid = st.number_input("Product ID to update", min_value=1, value=66667, step=1, key="u_id")
        row = run_query("SELECT * FROM flipkart_other_products WHERE product_id = :id", {"id": int(pid)})

        if row.empty:
            st.warning("No product with this ID.")
        else:
            current = row.iloc[0]
            st.write(f"**{current['product_name']}**  ({current['category']} / {current['sub_category']})")

            # the key includes the product ID, so the boxes refill when a different ID is entered
            col1, col2 = st.columns(2)
            with col1:
                upd_retail = st.number_input("Retail price (₹)", min_value=1.0,
                                             value=float(current["retail_price"]), step=100.0, key=f"u_retail_{pid}")
                upd_pct = st.number_input("Discount %", min_value=0.0, max_value=100.0,
                                          value=float(current["discount_percentage"]), step=0.5, key=f"u_pct_{pid}")
                upd_stock = st.selectbox("Stock status", STOCK_OPTIONS,
                                         index=STOCK_OPTIONS.index(current["stock_status"]), key=f"u_stock_{pid}")
            with col2:
                upd_rating = st.number_input("Rating", min_value=0.0, max_value=5.0,
                                             value=float(current["rating"]), step=0.1, key=f"u_rating_{pid}")
                upd_reviews = st.number_input("Number of reviews", min_value=0,
                                              value=int(current["num_reviews"]), step=1, key=f"u_reviews_{pid}")

            discount_price, discount_amount = calculate_prices(upd_retail, upd_pct)

            if st.button("Update product", type="primary", key="u_button"):
                run_change("""
                    UPDATE flipkart_other_products
                    SET retail_price = :retail, discount_percentage = :pct,
                        discount_price = :dprice, discount_amount = :damount, price_difference = :damount,
                        rating = :rating, num_reviews = :reviews, stock_status = :stock,
                        rating_category = :rcat, discount_range = :drange
                    WHERE product_id = :id
                """, {
                    "retail": upd_retail, "pct": upd_pct, "dprice": discount_price, "damount": discount_amount,
                    "rating": upd_rating, "reviews": int(upd_reviews), "stock": upd_stock,
                    "rcat": get_rating_category(upd_rating), "drange": get_discount_range(upd_pct), "id": int(pid),
                })
                st.success(f"Product {int(pid)} updated.")
                st.dataframe(run_query("SELECT * FROM flipkart_other_products WHERE product_id = :id",
                                       {"id": int(pid)}), hide_index=True)

    # ---------------- DELETE ----------------
    with delete_tab:
        st.subheader("Delete a product")
        pid = st.number_input("Product ID to delete", min_value=1, value=66667, step=1, key="d_id")
        row = run_query("SELECT * FROM flipkart_other_products WHERE product_id = :id", {"id": int(pid)})

        if row.empty:
            st.warning("No product with this ID.")
        else:
            st.dataframe(row, hide_index=True)
            confirm = st.checkbox("Yes, I want to delete this product", key="d_confirm")
            if st.button("Delete product", type="primary", key="d_button"):
                if not confirm:
                    st.error("Tick the confirmation box first.")
                else:
                    run_change("DELETE FROM flipkart_other_products WHERE product_id = :id", {"id": int(pid)})
                    st.success(f"Product {int(pid)} deleted.")


# ============================================================
# 10. SHOW THE SELECTED PAGE
# ============================================================
if page == "Dashboard":
    show_dashboard(sidebar_filters(products))
elif page == "Data Explorer":
    show_data_explorer(sidebar_filters(products))
elif page == "Analysis":
    show_analysis(sidebar_filters(products), sellers)
elif page == "SQL Query Explorer":
    show_sql_explorer()
elif page == "CRUD Operations":
    show_crud()
