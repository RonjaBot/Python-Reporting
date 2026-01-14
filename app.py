import streamlit as st
import pandas as pd
import pg8000
import plotly.express as px

st.set_page_config(page_title="Pagila DWH Reporting", layout="wide")
st.title("Pagila DWH Reporting")

# --------- DB ----------
def get_conn():
    return pg8000.connect(
        host="localhost",
        database="pagila_dwh",
        user="postgres",
        password="hello1234",
        port=5432,
    )

@st.cache_data(ttl=60)
def get_view_columns() -> set[str]:
    """Return column names of vw_rental_analysis (lowercased)."""
    q = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name='vw_rental_analysis'
    ORDER BY ordinal_position;
    """
    with get_conn() as conn:
        cols = pd.read_sql(q, conn)["column_name"].str.lower().tolist()
    return set(cols)

@st.cache_data(ttl=60)
def distinct_values(col: str):
    with get_conn() as conn:
        df = pd.read_sql(f"SELECT DISTINCT {col} FROM vw_rental_analysis ORDER BY {col};", conn)
    return df.iloc[:, 0].dropna().tolist()

def build_in_clause(col: str, values: list):
    """Build 'col IN (%s,%s,...)' and params."""
    placeholders = ", ".join(["%s"] * len(values))
    return f"{col} IN ({placeholders})", values

# --------- Sidebar Filters ----------
cols = get_view_columns()

st.sidebar.header("Filters")

# Metric toggle (passt immer)
metric = st.sidebar.selectbox("Metric", ["total_rentals", "total_revenue"], index=0)

# Time granularity: month vs quarter (quarter nur, wenn quarter existiert ODER month existiert)
time_grain = "month"
if "month" in cols and "year" in cols:
    time_grain = st.sidebar.radio("Time grain (trend)", ["month", "quarter"], horizontal=True, index=0)

# Top-N für Report 1 
top_n = st.sidebar.slider("Top N categories (Report 1)", min_value=5, max_value=25, value=10, step=1)

filters_sql = []
params = []

# Year filter 
selected_years = []
if "year" in cols:
    years = distinct_values("year")
    selected_years = st.sidebar.multiselect("Year", options=years, default=years)
    if selected_years and len(selected_years) != len(years):
        clause, p = build_in_clause("year", selected_years)
        filters_sql.append(clause)
        params.extend(p)

# Category filter 
selected_cats = []
if "film_category" in cols:
    cats = distinct_values("film_category")
    selected_cats = st.sidebar.multiselect("Film category", options=cats, default=cats)
    if selected_cats and len(selected_cats) != len(cats):
        clause, p = build_in_clause("film_category", selected_cats)
        filters_sql.append(clause)
        params.extend(p)

# Optional: Rating filter (nur wenn vorhanden)
if "film_rating" in cols:
    ratings = distinct_values("film_rating")
    selected_ratings = st.sidebar.multiselect("Film rating", options=ratings, default=ratings)
    if selected_ratings and len(selected_ratings) != len(ratings):
        clause, p = build_in_clause("film_rating", selected_ratings)
        filters_sql.append(clause)
        params.extend(p)

# Optional: Store filter (nur wenn vorhanden)
# (je nach View können das z.B. store_id, store_city, store_country heißen – wir checken robust)
store_col = None
for candidate in ["store_id", "store_city", "store_country"]:
    if candidate in cols:
        store_col = candidate
        break

if store_col:
    stores = distinct_values(store_col)
    default = stores
    selected_stores = st.sidebar.multiselect(f"{store_col}", options=stores, default=default)
    if selected_stores and len(selected_stores) != len(stores):
        clause, p = build_in_clause(store_col, selected_stores)
        filters_sql.append(clause)
        params.extend(p)

where_sql = ""
if filters_sql:
    where_sql = "WHERE " + " AND ".join(filters_sql)

# --------- Report 1: Rentals by Film Category ----------
st.header("Report 1: Rentals by Film Category")
st.sidebar.caption("Tip: Filters affect both reports.")

# Für Report 1 brauchen wir film_category und rental_amount (für revenue)
if "film_category" not in cols:
    st.error("vw_rental_analysis has no column 'film_category'. Cannot build Report 1 from the view.")
else:
    query1 = f"""
    SELECT film_category,
           COUNT(*) AS total_rentals,
           SUM(rental_amount) AS total_revenue
    FROM vw_rental_analysis
    {where_sql}
    GROUP BY film_category
    ORDER BY total_rentals DESC
    LIMIT {top_n};
    """
    with get_conn() as conn:
        df1 = pd.read_sql(query1, conn, params=params)

    if df1.empty:
        st.warning("No data for the selected filters.")
    else:
        # --- Summary stats (Report 1) ---
        total_rentals = int(df1["total_rentals"].sum())
        total_revenue = float(df1["total_revenue"].sum())

        top_row = df1.sort_values("total_rentals", ascending=False).iloc[0]
        top_cat = str(top_row["film_category"])
        top_cat_rentals = int(top_row["total_rentals"])
        top_cat_revenue = float(top_row["total_revenue"])

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total rentals (filtered)", f"{total_rentals:,}")
        k2.metric("Total revenue (filtered)", f"${total_revenue:,.2f}")
        k3.metric("Top category (rentals)", top_cat)
        k4.metric("Top category rentals", f"{top_cat_rentals:,}")

        # Chart
        pretty_metric_label = "Total rentals" if metric == "total_rentals" else "Total revenue"

        fig1 = px.bar(
            df1,
            x="film_category",
            y=metric,
            title=f"Rentals by Film Category ({pretty_metric_label})",
            labels={
                "film_category": "Film category",
                metric: pretty_metric_label,
            },
            hover_data={
                "film_category": True,
                "total_rentals": True,
                "total_revenue": ":.2f",
            },
        )

        fig1.update_layout(
            xaxis_title="Film category",
            yaxis_title=pretty_metric_label,
            bargap=0.5,
            height=520,
            margin=dict(l=40, r=20, t=70, b=80),
        )

        fig1.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Rentals: %{customdata[0]:,}<br>"
                "Revenue: $%{customdata[1]:,.2f}<extra></extra>"
            ),
            customdata=df1[["total_rentals", "total_revenue"]].values,
        )

    if metric == "total_revenue":
        fig1.update_yaxes(tickprefix="$", tickformat=",")
    else:
        fig1.update_yaxes(tickformat=",")

    fig1.update_xaxes(tickangle=-35)
    fig1.update_xaxes(categoryorder="total descending")

    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("Show data (Report 1)"):
        st.dataframe(df1, use_container_width=True)


# --------- Report 2: Rental Trends Over Time ----------
st.header("Report 2: Rental Trends Over Time")

if "year" not in cols:
    st.error("vw_rental_analysis has no column 'year'. Cannot build Report 2 from the view.")
else:
    if time_grain == "quarter":
        # Quarter entweder direkt vorhanden, oder wir berechnen ihn aus month
        if "quarter" in cols:
            time_select = "year, quarter"
            time_group = "year, quarter"
            time_order = "year, quarter"
            period_expr = "CAST(year AS text) || '-Q' || CAST(quarter AS text) AS period"
        else:
            if "month" not in cols:
                st.error("No 'quarter' column and no 'month' column to compute quarter. Switch time grain to month.")
                st.stop()
            time_select = "year, ((month - 1) / 3 + 1) AS quarter"
            time_group = "year, ((month - 1) / 3 + 1)"
            time_order = "year, ((month - 1) / 3 + 1)"
            period_expr = "CAST(year AS text) || '-Q' || CAST(((month - 1) / 3 + 1) AS text) AS period"

        query2 = f"""
        SELECT {time_select},
               COUNT(*) AS total_rentals,
               SUM(rental_amount) AS total_revenue,
               {period_expr}
        FROM vw_rental_analysis
        {where_sql}
        GROUP BY {time_group}
        ORDER BY {time_order};
        """
    else:
        if "month" not in cols:
            st.error("vw_rental_analysis has no column 'month'. Cannot build monthly trend.")
            st.stop()
        query2 = f"""
        SELECT year, month,
               COUNT(*) AS total_rentals,
               SUM(rental_amount) AS total_revenue,
               CAST(year AS text) || '-' || LPAD(CAST(month AS text), 2, '0') AS period
        FROM vw_rental_analysis
        {where_sql}
        GROUP BY year, month
        ORDER BY year, month;
        """

    with get_conn() as conn:
        df2 = pd.read_sql(query2, conn, params=params)

    if df2.empty:
        st.warning("No trend data for the selected filters.")
    else:
        # --- Summary stats (Report 2) ---
        first_period = str(df2["period"].iloc[0])
        last_period = str(df2["period"].iloc[-1])

        peak_idx = df2[metric].idxmax()
        peak_period = str(df2.loc[peak_idx, "period"])
        peak_value = float(df2.loc[peak_idx, metric])

        avg_value = float(df2[metric].mean())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Period range", f"{first_period} → {last_period}")

        if metric == "total_revenue":
            c2.metric("Total (filtered)", f"${df2[metric].sum():,.2f}")
            c3.metric("Average per period", f"${avg_value:,.2f}")
            c4.metric("Peak period", f"{peak_period} (${peak_value:,.2f})")
        else:
            c2.metric("Total (filtered)", f"{int(df2[metric].sum()):,}")
            c3.metric("Average per period", f"{avg_value:,.0f}")
            c4.metric("Peak period", f"{peak_period} ({int(peak_value):,})")
        
        # Chart
        pretty_metric_label = "Total rentals" if metric == "total_rentals" else "Total revenue"

        fig2 = px.line(
            df2,
            x="period",
            y=metric,
            title=f"Rental trends over time ({pretty_metric_label})",
            labels={
                "period": "Period",
                metric: pretty_metric_label,
            },
            markers=True,
        )

        fig2.update_layout(
            xaxis_title="Period",
            yaxis_title=pretty_metric_label,
            height=520,
            margin=dict(l=40, r=20, t=70, b=60),
        )

        fig2.update_yaxes(rangemode="tozero", automargin=True)
        fig2.update_xaxes(tickangle=-30)

        fig2.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{pretty_metric_label}: " + ("%{y:,.2f}" if metric=="total_revenue" else "%{y:,}") +
                ("<extra></extra>")
            )
        )

        if metric == "total_revenue":
            fig2.update_yaxes(tickprefix="$", tickformat=",")
        else:
            fig2.update_yaxes(tickformat=",")

        # keep x readable (especially for many periods)
        fig2.update_xaxes(type="category")

        st.plotly_chart(fig2, use_container_width=True)

        mean_val = df2[metric].mean()
        fig2.add_hline(y=mean_val, line_dash="dot", annotation_text="Average", annotation_position="top left")


