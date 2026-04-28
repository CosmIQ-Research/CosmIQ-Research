import streamlit as st
import psycopg
import pandas as pd
import plotly.express as px
import time

# Connect to Neon
@st.cache_data
def load_data():
    conn_str = (
        "postgresql://neondb_owner:npg_o0HsChQ4lkSa"
        "@ep-holy-unit-a5k4mdnx-pooler.us-east-2.aws.neon.tech/neondb"
        "?sslmode=require&options=endpoint%3Dep-holy-unit-a5k4mdnx-pooler"
    )
    with psycopg.connect(conn_str) as conn:
        brands = pd.read_sql_query("SELECT * FROM brands", conn)
        products = pd.read_sql_query("SELECT * FROM products", conn)
        return brands, products

# Load data
brands, products = load_data()

# App Layout
st.title("CosmIQ Dashboard")
st.sidebar.header("Filters")
brand_filter = st.sidebar.multiselect("Select Brand", brands["name"].unique())

# Filtered Data
if brand_filter:
    selected_brands = brands[brands["name"].isin(brand_filter)]
    filtered_products = products[products["brand_id"].isin(selected_brands["brand_id"])]
else:
    filtered_products = products

# Visuals
st.subheader("Product Count by Brand")
prod_counts = filtered_products["brand_id"].value_counts().reset_index()
prod_counts.columns = ["brand_id", "count"]
prod_counts = prod_counts.merge(brands, left_on="brand_id", right_on="brand_id")
fig = px.bar(prod_counts, x="name", y="count", title="Number of Products per Brand")
st.plotly_chart(fig)

# Table
st.subheader("Product Table")
st.dataframe(filtered_products[["name", "category", "is_clean_labeled"]])
