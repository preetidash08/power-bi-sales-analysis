# power-bi-sales-analysis
Power BI dashboard analyzing sales performance and regional profit margins
# power-bi-sales-analysis
Power BI dashboard analyzing sales performance and regional profit margins

## 📊 Executive Summary
This Power BI project is an end-to-end Sales Performance Analytics Dashboard designed to provide a comprehensive view of business performance across sales, profitability, products, customers, sales representatives, regions, channels, and market segments.

The dashboard analyzes sales data from January 2024 to December 2025 and enables stakeholders to monitor key business KPIs, identify performance trends, and uncover actionable insights to support data-driven decision-making.

Key Metrics Analyzed
Total Net Sales
Gross Profit
Gross Margin %
Units Sold
Return Rate
On-Time Delivery %
Target Attainment %
Year-over-Year Sales
Month-to-Date Sales
Rolling 3-Month Sales
Average Discount %
Average NPS
Dashboard Analysis Areas

The report includes multiple interactive views covering:

Sales Overview: Tracks overall sales performance against targets, monthly sales trends, profitability, returns, delivery performance, and year-over-year performance.

Sales Representative Performance: Evaluates individual sales representatives based on net sales, gross margin, return rate, target attainment, and tenure. The analysis also helps identify top performers, volume drivers, high-risk performers, and the relationship between discounting and profitability.

Product Performance: Compares Hardware, Services, and Software across revenue, gross profit, gross margin, return rates, units sold, and discounts.

Customer & Market Analysis: Provides insights into customer segments, industries, channels, cities, customer value, NPS, and delivery performance.

Tools & Technologies
Power BI Desktop
DAX
Data Modeling and Star Schema Design
Exploratory Data Analysis
Business KPI Development
Data Visualization and Dashboard Design

The dashboard was designed to enable interactive analysis through filters for Region, Segment, Channel, Product Category, and Date, allowing users to drill into performance across different business dimensions.
---

## 🛠️ Tools & Tech Stack
- **Business Intelligence:** Power BI Desktop
- **Data Transformation:** Power Query
- **Calculations:** DAX (Data Analysis Expressions)

---

## 🔑 Key DAX Measures & Source Code
Below are examples of core measures written for this model:
Net Sales=  SUM(Orders[Net_Sales_INR])

