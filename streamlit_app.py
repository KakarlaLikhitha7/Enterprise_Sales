ENTERPRISE_DB.GOLD.ENTERPRISE_SALESimport streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(page_title="Enterprise Time KPIs", layout="wide")
st.title("📊 Enterprise Sales – Advanced Time Analytics")

session = get_active_session()

# -------------------------------------------------
# Load Data
# -------------------------------------------------
@st.cache_data(ttl=600)
def load_data():
    return session.sql("""
        SELECT *
        FROM ENTERPRISE_DB.GOLD.VW_TIME_SALES_KPI
        ORDER BY Order_Date
    """).to_pandas()

df = load_data()

if df.empty:
    st.error("No data available")
    st.stop()

df["ORDER_DATE"] = pd.to_datetime(df["ORDER_DATE"])

# -------------------------------------------------
# 🔥 MAIN PAGE – TIME GRANULARITY
# -------------------------------------------------
st.subheader("⏱ Time Granularity")

time_grain = st.radio(
    "",
    ["Monthly", "Quarterly", "Half-Yearly", "Yearly"],
    horizontal=True
)

st.divider()

# -------------------------------------------------
# Sidebar Controls (Filters only)
# -------------------------------------------------
st.sidebar.header("🎛 Filters")

year_filter = st.sidebar.multiselect(
    "Select Year(s)",
    sorted(df["YEAR"].unique()),
    default=sorted(df["YEAR"].unique())
)

cumulative = st.sidebar.checkbox("📈 Show Cumulative Sales")
show_growth = st.sidebar.checkbox("📊 Show Growth %")
sort_order = st.sidebar.radio("Sort Order", ["Ascending", "Descending"])

df = df[df["YEAR"].isin(year_filter)]

# -------------------------------------------------
# Aggregation Logic
# -------------------------------------------------
if time_grain == "Monthly":
    group_cols = ["YEAR", "MONTH"]
elif time_grain == "Quarterly":
    group_cols = ["YEAR", "QUARTER"]
elif time_grain == "Half-Yearly":
    group_cols = ["YEAR", "HALF_YEAR"]
else:
    group_cols = ["YEAR"]

agg_df = (
    df.groupby(group_cols)["REVENUE"]
      .sum()
      .reset_index()
)

# Sorting
agg_df = agg_df.sort_values(
    group_cols,
    ascending=(sort_order == "Ascending")
)

# Cumulative logic
if cumulative:
    agg_df["REVENUE"] = agg_df["REVENUE"].cumsum()

# Growth %
if show_growth:
    agg_df["GROWTH_%"] = agg_df["REVENUE"].pct_change() * 100

# -------------------------------------------------
# KPI Cards
# -------------------------------------------------
c1, c2, c3 = st.columns(3)

c1.metric("💰 Total Revenue", f"{df['REVENUE'].sum():,.2f}")
c2.metric("📆 Periods", len(agg_df))
c3.metric("📊 View", time_grain)

# -------------------------------------------------
# Visualization
# -------------------------------------------------
st.subheader(f"📈 {time_grain} Sales Analysis")

if show_growth:
    st.line_chart(agg_df, y="GROWTH_%")
else:
    if time_grain in ["Monthly", "Yearly"]:
        st.line_chart(agg_df, y="REVENUE")
    else:
        st.bar_chart(agg_df, y="REVENUE")

# -------------------------------------------------
# Insights Section
# -------------------------------------------------
with st.expander("📌 Key Insights"):
    st.write(f"""
    • Time granularity: **{time_grain}**  
    • Years selected: **{', '.join(map(str, year_filter))}**  
    • Cumulative mode: **{"Enabled" if cumulative else "Disabled"}**  
    • Growth mode: **{"Enabled" if show_growth else "Disabled"}**
    """)

# -------------------------------------------------
# Download Option
# -------------------------------------------------
with st.expander("⬇ Download Aggregated Data"):
    csv = agg_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="time_sales_kpi.csv",
        mime="text/csv"
    )

# -------------------------------------------------
# Raw Data
# -------------------------------------------------
with st.expander("🔍 View Aggregated Data"):
    st.dataframe(agg_df)
