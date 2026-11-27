# Flipkart Product Analytics & Business Intelligence Dashboard

An end-to-end data analytics project on Flipkart product data: raw JSON and CSV files are cleaned with Python and Pandas, stored in a MySQL database, analysed with SQL, and presented through an interactive Power BI dashboard and Streamlit app.

____________________________________________________________________________________________________________________________________________________________________________________________________________________

## Project Objectives 🎯

- Extract and understand product data from JSON and CSV files.
- Identify and handle missing values, duplicates, and inconsistent data.
- Clean and preprocess the data using Python and Pandas.
- Perform EDA to identify patterns and trends.
- Create derived columns for discount amount, price difference, rating category, and discount range.
- Store the cleaned data in MySQL tables.
- Perform SQL queries to analyse products, pricing, ratings, discounts, and seller performance.
- Create Power BI dashboards to visualize key metrics and trends.
- Develop an interactive Streamlit dashboard for data exploration and analysis.
- Generate meaningful business insights to support decision-making.

________________________________________________________________________________________________________________________________________________________________________________________________________________________

## Tech Stack 📌

Area	               | Tools                                                        |
|--------------------|--------------------------------------------------------------|
|Data cleaning & EDA	 | Python, Pandas, NumPy, Matplotlib, Seaborn, Jupyter Notebook |
|Database	           | MySQL, SQLAlchemy, PyMySQL                                   |
|Web app	             | Streamlit, streamlit-option-menu, Plotly                     |
|Visualisation        |	Power BI                                                    |

________________________________________________________________________________________________________________________________________________________________________________________________________________________

## Project Structure 📜
```
flipkart_product_analytics_dashboard/
|--Raw_Data/
|   |--flipkart_category_catalog.json
|   |--flipkart_other_products.csv
|   |--flipkart_seller_performance.json
|--Cleaned_Data/
|   |--category_catalog_cleaned.csv
|   |--other_products_cleaned.csv
|   |--seller_performance_cleaned.csv
|--flipkart_data_cleaning_final.ipynb  # cleaning, validation, EDA, MySQL loading
|--flipkart_db.sql                     # SQL business queries
|--app.py                              # Streamlit dashboard
|--requirements.txt                    # Python libraries
|--flipkart_product_analytics.pbix     # Power BI dashboard
|--flipkart_product_analytics_ business_insights_report.docx.         # business insights report
|--README.md.
```
________________________________________________________________________________________________________________________________________________________________________________________________________________________

## Dataset 📚

| File	| Format	| Records	|	Contents |
|-------|---------|---------|----------|
|flipkart_category_catalog.json   |	JSON (category → sub-category → products) |33,333 |	Prices, discounts, ratings, reviews, product URL|
|flipkart_seller_performance.json |	JSON (seller → products)	                |33,333 | Seller, rating, reviews, stock status           |
|flipkart_other_products.csv      |	CSV	                                      |33,334	|	Full product details including seller and stock status                |

________________________________________________________________________________________________________________________________________________________________________________________________________________________

## Workflow 📝
### 1. Data Cleaning (Jupyter Notebook) 🕵️‍♂️
- Flattened the deeply nested JSON files into tables.
- Brand, category, and subcategory mismatch: ~90% (30,033 of 33,333 in the catalog) of records had mismatches in brand, category, and subcategory. E.g., "Nike Leather Cricket Bat Top Grade (1)" was listed as Samsung brand in Electronics Category. Rebuilt the brand, category, and subcategory names using a mapping of the 10 base products.
- Changing Data Types: Converted the retail price, discount price, discount amount, price difference, rating, and number of reviews columns to numeric type.
- Pricing Issues: discount_price and discount_amount were inconsistent; discount_price was higher than retail_price in 30,135 rows. Rebuilt from retail_price and discount_percentage.
    - discount_price = retail_price x (1 - discount_percentage / 100)
    - discount_amount = price_difference = retail_price - discount_price
- Missing values: Checked for missing values and their distribution in all three files. 1,666 retail prices and 1,000 ratings were filled with the median of the same base product.
- Rating category was inconsistent in both the other_products and seller_performance tables. Recalculated for every row
    - Excellent: ≥ 4.5
    - Good: 4.0 - 4.4
    - Average: < 4.0
- Discount range: created a derived column, added (0-20%, 21-40%, 41-60%)
- Standardised column names: from review_count → num_reviews
- Data Integrity Check: validated all three cleaned files. No missing values, no duplicates, and all derived columns match their formulas.
- SQL Loading: created the flipkart_db database in MySQL using the SQLAlchemy and pymysql libraries.

### 2. MySQL Database 🔗
Database flipkart_db with three tables, each with product_id as the primary key:

|Table	                 | Rows  |
|------------------------|-------|
|flipkart_other_products | 33,334|
|category_catalog	      | 33,333|
|seller_performance	    |33,333|

After loading, verified record counts and data integrity (primary keys, missing values, price rules, value ranges).

### 3. SQL Analysis 📊
flipkart_db.sql contains 19 business queries, including:
- Total listings, average rating, price, and discount statistics
- Listings and average discount by category and sub-category
- Categories and brands with more than N listings (HAVING)
- Products above the average discount price (subquery)
- All product tables combined with UNION ALL
- A seller-summary view joined to product listings (JOIN)

### 4. Power BI Dashboard 📊
- __MySQL connection:__ imported data from the MySQL database using the MySQL connector and loaded all three files: category_catalog, flipkart_other_products, seller_performance
- __Appending Tables:__ appended flipkart_other_products table with category_catalog table and created a new table as all_products
- __Data Modeling:__ 1-to-1 relationship between flipkart_other_products and all_products table through product_id as key. The seller performance table's product_id doesn't overlap with the other tables.
<img width="550" height="358" alt="image" src="https://github.com/user-attachments/assets/6f96b378-85ac-48fd-8b92-1810ffbc3185" />

- __Five report pages:__ Product & Category Analysis, Pricing & Discounts, Ratings & Reviews, Seller Performance, and Product Priority. Together, they answer all 20 sample visualisation questions from the project brief.
- __Product & Category Analysis:__ tracks 4 core KPIs (Total Products, Average Retail Price, Average Rating, and Average Discount Percentage) alongside 4 analytical views: Total products by category & subcategory, Total products by brand, Rating category, and Category-subcategory breakdown. Interactive slicers for Category, Subcategory, and Brand allow for dynamic data filtering.
<img width="1250" height="730" alt="image" src="https://github.com/user-attachments/assets/732295f7-af11-4c7d-b97c-78982c7b2917" />

- __Pricing & Discounts:__ tracks 1 core KPIs (Average Discount Amount) alongside 4 analytical views: Average Retail vs Discount Price by Category, Average Discount % by Category, Products by Discount Range, Top 10 Products by Discount Amount. Interactive slicer for Retail Price, Category, Subcategory, and Brand allow for dynamic data filtering.
<img width="1250" height="730" alt="image" src="https://github.com/user-attachments/assets/790dd796-994b-4184-9a67-ff900e030a7f" />

- __Ratings & Reviews:__ Provides 4 analytical views on ratings and reviews: Average Rating by Category, Top 10 Products by Number of Reviews, Rating vs. Average No. of Reviews, Products by Rating Category. The report includes interactive slicers for Category, Subcategory, and Brand.
<img width="1250" height="730" alt="image" src="https://github.com/user-attachments/assets/d181ceb1-d7b7-4c2c-8cc2-4b420cf29cd7" />

- __Seller Performance:__ tracks 2 core KPIs (Count of Sellers, Out-of-Stock Products) alongside 4 analytical views: Product Listing by Seller, Average Rating by Seller, Average Discount % by Seller, and Stock Status by Seller. The report is provided with two interactive slicers for Seller Name and Stock Status. 
<img width="1250" height="730" alt="image" src="https://github.com/user-attachments/assets/39bafb53-e8a3-4e9e-85b8-43f0e6017075" />

- __Product Priority:__ tracks 1 core KPI (Priority Products Count) alongside 3 analytical views: Rating vs Discounts by Category, Top Priority Products Lists, Share of Priority Products by Category %. The report is provided with three interactive slicers on Category, Subcategory, and Brand.
<img width="1250" height="730" alt="image" src="https://github.com/user-attachments/assets/ae49d435-4b1c-4e22-abed-f4cac1767555" />

### 5. Streamlit App 💻
| Page | Features |
|------|----------|
|Dashboard | KPI cards, products by category, stock status, rating categories, discount ranges |
| Data Explorer | Filtered product table, name search, CSV download |
| Analysis | Tabs for product, category, brand, pricing, discount, and seller analysis |
| SQL Query Explorer | Run any of the business queries and view the results |
| CRUD Operations | Create, read, update, and delete products in MySQL |

Sidebar filters: category, sub-category, brand, seller, stock status, rating, price range, and discount range.

<img width="1250" height="730" alt="image" src="https://github.com/user-attachments/assets/86fbfb16-7a9e-4ca2-aa1e-a2764d98e887" />

________________________________________________________________________________________________________________________________________________________________________________________________________________________

## Key Insights 📊
- Electronics holds 60% of the 66,667 priced listings; 5 of the 9 subcategories belong to it
- Every category averages about ₹75,600 retail price, a 32.5% discount, and a 4.0 rating
- 47% of products are rated below 4.0, and only 27% are rated Excellent
- Rating has no relationship with review count (correlation 0.003)
- Three sellers carry 60% of seller listings, but all seven sellers have similar ratings, discounts, and stock availability (about 10% out of stock)
- 3,262 products (4.9%) combine a 4.5+ rating, a 40%+ discount, and above-average reviews, making them the strongest candidates for promotion

See flipkart_product_analytics_business_insights_report.docx for the full analysis and recommendations.

________________________________________________________________________________________________________________________________________________________________________________________________________________________

## Setup Instructions 📜

### Prerequisites
- Python 3.10 or later
- MySQL Server 8.0 or later, plus MySQL Workbench (optional)
- Power BI Desktop (to open the .pbix file)
- Git

### 1. Clone the repository
```bash
git clone https://github.com/vijayhariharanbk/flipkart_product_analytics_dashboard.git
cd flipkart_product_analytics_dashboard
```
### 2. Install the Python libraries
```
`pip install -r requirements.txt`
```
### 3. Configure the database

Create the database in MySQL:
```sql
`CREATE DATABASE flipkart_db;`
```
Then set your MySQL username and password in two places:

- Notebook (MySQL loading section):
```python
engine = create_engine("mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/flipkart_db")
```
- app.py (section 1, Database settings):
```
DB_USER = "root"
DB_PASSWORD = "YOUR_PASSWORD"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "flipkart_db"
```
### 4. Clean the data and load it into MySQL

Open `flipkart_data_cleaning_final.ipynb`, set the raw data folder path in the load cells, and run all cells. This saves the three cleaned CSV files and creates the three MySQL tables.

### 5. Run the SQL queries

Open `flipkart_db.sql` in MySQL Workbench and run it against flipkart_db.

### 6. Start the Streamlit app
```
streamlit run app.py
```
The app opens in your browser at http://localhost:8501.

### 7. Open the Power BI dashboard

- Open `flipkart_product_analytics.pbix` in Power BI Desktop. If prompted, update the MySQL connection (Home → Transform data → Data source settings) and click Refresh.

________________________________________________________________________________________________________________________________________________________________________________________________________________________

## Troubleshooting 🕵️‍♂️
| Error                          |	Fix                                         |
|--------------------------------|----------------------------------------------|
| Access denied for user 'root'	 | Check the password in the notebook and app.py|
| Can't connect to MySQL server  | Start the MySQL service                      |
| Unknown database 'flipkart_db' | Run CREATE DATABASE flipkart_db;             |
| ModuleNotFoundError            | Run pip install -r requirements.txt          |
| SQLAlchemy ImportError mentioning a blocked file (Windows) |	Reinstall SQLAlchemy without compiled extensions: $env:DISABLE_SQLALCHEMY_CEXT="1" then pip install --force-reinstall --no-deps --no-binary sqlalchemy sqlalchemy

## Author
### Vijay
