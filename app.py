import streamlit as st
import pandas as pd
import pg8000
import plotly.express as px

st.title("Pagila DWH Reporting")

def get_conn():
    return pg8000.connect(
        host="localhost",
        database="pagila_dwh",
        user="postgres",
        password="hello1234",
        port=5432,
    )

# -------- Report 1 --------
st.header("Report 1: Rentals by Film Category")

query1 = """
SELECT film_category,
       COUNT(*) AS total_rentals,
       SUM(rental_amount) AS total_revenue
FROM vw_rental_analysis
GROUP BY film_category
ORDER BY total_rentals DESC;
"""

with get_conn() as conn:
    df1 = pd.read_sql(query1, conn)

metric1 = st.selectbox("Metric", ["total_rentals", "total_revenue"])
fig1 = px.bar(df1, x="film_category", y=metric1)
st.plotly_chart(fig1, use_container_width=True)

# -------- Report 2 --------
st.header("Report 2: Rental Trends Over Time")

query2 = """
SELECT year, month, month_name,
       COUNT(*) AS total_rentals,
       SUM(rental_amount) AS total_revenue
FROM vw_rental_analysis
GROUP BY year, month, month_name
ORDER BY year, month;
"""

with get_conn() as conn:
    df2 = pd.read_sql(query2, conn)

df2["period"] = df2["year"].astype(str) + "-" + df2["month"].astype(str).str.zfill(2)

metric2 = st.selectbox("Metric (Trend)", ["total_rentals", "total_revenue"])
fig2 = px.line(df2, x="period", y=metric2)
st.plotly_chart(fig2, use_container_width=True)
