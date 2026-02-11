import streamlit as st
import pandas as pd
from snowflake.snowpark import Session

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="Enterprise Sales Analytics",
    layout="wide"
)

st.title("📊 Enterprise Sales – Gold Layer Analytics")

# -------------------------------------------------
# Snowflake Connection
# -------------------------------------------------
@st.cache_resource
def get_snowflake_session():
    connection_parameters = {
        "account": st.secrets["snowflake"]["account"],
        "user": st.secrets["snowflake"]["user"],
        "password": st.secrets["snowflake"]["password"],
        "role": st.secrets["snowflake"]["role"],
        "warehouse": st.secrets["snowflake"]["warehouse"],
        "database": st.secrets["snowflake"]["database"],
        "schema": st.secrets["snowflake"]["schema"]
    }
    return Session.builder.configs(connection_parameters).create()

session = get_snowflake_session()

# -------------------------------------------------
# Sidebar Controls
# -------------------------------------------------
st.sidebar.header("🎛 Controls")

time_grain = st.sidebar.radio(
    "Select Time Granularity",
    ["Monthly", "Quarterly", "Half-Yearly", "Yearly"]
)

sort_order = st.sidebar.radio(
    "Sort Order",
    ["Ascending", "Descending"]
)

show_growth = st.sidebar.checkbox("📈 Show Growth %")
cumulative = st.sidebar.checkbox("📊 Cumulative Revenue")

# -------------------------------------------------
# Data Loader
# -------------------------------------------------
@st.cache_data(ttl=600)
def load_data(grain):
    if grain == "Monthly":
        query = """
            SELECT YEAR, MONTH, MONTHLY_REVENUE AS REVENUE
            FROM GOLD.MONTHLY_SALES
        """
    elif grain == "Quarterly":
        query = """
            SELECT YEAR, QUARTER, QUARTERLY_REVENUE AS REVENUE
            FROM GOLD.QUARTERLY_SALES
        """
    elif grain == "Half-Yearly":
        query = """
            SELECT YEAR, HALF_YEAR, HALF_YEARLY_REVENUE AS REVENUE
            FROM GOLD.HALF_YEARLY_SALES
        """
    else:
        query = """
            SELECT YEAR, YEARLY_REVENUE AS REVENUE
            FROM GOLD.YEARLY_SALES
        """

    return session.sql(query).to_pandas()

df = load_data(time_grain)

if df.empty:
    st.error("No data available")
    st.stop()

# -------------------------------------------------
# Filters
# -------------------------------------------------
years = sorted(df["YEAR"].unique())
selected_years = st.sidebar.multiselect(
    "Select Year(s)",
    years,
    default=years
)

df = df[df["YEAR"].isin(selected_years)]

ascending = sort_order == "Ascending"

if time_grain == "Monthly":
    df = df.sort_values(["YEAR", "MONTH"], ascending=ascending)
elif time_grain == "Quarterly":
    df = df.sort_values(["YEAR", "QUARTER"], ascending=ascending)
elif time_grain == "Half-Yearly":
    df = df.sort_values(["YEAR", "HALF_YEAR"], ascending=ascending)
else:
    df = df.sort_values("YEAR", ascending=ascending)

# -------------------------------------------------
# Calculations
# -------------------------------------------------
if cumulative:
    df["REVENUE"] = df["REVENUE"].cumsum()

if show_growth:
    df["GROWTH_%"] = df["REVENUE"].pct_change() * 100

# -------------------------------------------------
# KPI Cards
# -------------------------------------------------
c1, c2, c3 = st.columns(3)

c1.metric("💰 Total Revenue", f"{df['REVENUE'].sum():,.2f}")
c2.metric("📆 Periods", len(df))
c3.metric("⏱ Time Grain", time_grain)

st.divider()

# -------------------------------------------------
# Charts
# -------------------------------------------------
st.subheader(f"📈 {time_grain} Sales Trend")

if show_growth:
    st.line_chart(df, y="GROWTH_%")
else:
    if time_grain in ["Monthly", "Yearly"]:
        st.line_chart(df, y="REVENUE")
    else:
        st.bar_chart(df, y="REVENUE")

# -------------------------------------------------
# Download
# -------------------------------------------------
with st.expander("⬇ Download Data"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        csv,
        f"{time_grain.lower()}_sales.csv",
        "text/csv"
    )

# -------------------------------------------------
# Preview
# -------------------------------------------------
with st.expander("🔍 Data Preview"):
    st.dataframe(df)
