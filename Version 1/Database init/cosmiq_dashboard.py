import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
brands_df = pd.read_csv("brands_starter.csv")
products_df = pd.read_csv("products.csv")
ingredients_df = pd.read_csv("ingredients.csv")

# Add placeholder columns if missing
ingredients_df["toxicity_score"] = ingredients_df.get("toxicity_score", 5)
ingredients_df["synthetic_flag"] = ingredients_df.get("synthetic_flag", False)

st.title("CosmIQ Interactive Dashboard")

# Sidebar filters
st.sidebar.header("Filters")
selected_brand = st.sidebar.multiselect(
    "Select Brand(s)",
    brands_df["name"].unique()
)
selected_category = st.sidebar.multiselect(
    "Select Category(ies)",
    products_df["category"].dropna().unique()
)
clean_filter = st.sidebar.radio(
    "Clean Labeled?",
    ["All", True, False],
    index=0
)

# Ensure brand_id columns are the same type
brands_df["brand_id"] = brands_df["brand_id"].astype(str)
products_df["brand_id"] = products_df["brand_id"].astype(str)

# Merge products with brands
products_df = products_df.merge(brands_df, on="brand_id", how="left")

# Apply filters
filtered_products = products_df.copy()
if selected_brand:
    filtered_products = filtered_products[filtered_products["name_y"].isin(selected_brand)]
if selected_category:
    filtered_products = filtered_products[filtered_products["category"].isin(selected_category)]
if clean_filter != "All":
    filtered_products = filtered_products[filtered_products["is_clean_labeled"] == clean_filter]

# Product Count by Brand
st.subheader("Product Count by Brand")
brand_counts = filtered_products["name_y"].value_counts().reset_index()
brand_counts.columns = ["Brand", "Product Count"]
fig1 = px.bar(brand_counts, x="Brand", y="Product Count", title="Products per Brand")
st.plotly_chart(fig1)

# Clean vs Non-Clean Pie Chart
st.subheader("Clean Labeled Distribution")
clean_counts = filtered_products["is_clean_labeled"].value_counts().reset_index()
clean_counts.columns = ["Clean Labeled", "Count"]
fig2 = px.pie(clean_counts, names="Clean Labeled", values="Count", title="Clean vs Non-Clean Products")
st.plotly_chart(fig2)

# Toxicity Scatter Plot
st.subheader("Ingredient Toxicity Chart")
fig4 = px.scatter(
    ingredients_df,
    x="toxicity_score",
    y="toxicity_score",  # For placeholder purposes
    color="synthetic_flag",
    hover_data=["inci_name"],
    title="Toxicity Score Distribution (Placeholder)"
)
st.plotly_chart(fig4)

# Show data table
st.subheader("Filtered Product Data")
st.dataframe(filtered_products)
