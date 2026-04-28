import streamlit as st
import psycopg
import pandas as pd
import plotly.express as px

# Connect to PostgreSQL
def get_connection():
    return psycopg.connect(
        "postgresql://neondb_owner:npg_o0HsChQ4lkSa"
        "@ep-holy-unit-a5k4mdnx-pooler.us-east-2.aws.neon.tech/neondb"
        "?sslmode=require&options=endpoint%3Dep-holy-unit-a5k4mdnx-pooler"
    )

# Load ingredients
@st.cache_data
def load_ingredients():
    with get_connection() as conn:
        df = pd.read_sql_query("""
            SELECT ingredient_id, inci_name, type_origin, inci_complexity, source_info, 
                   sds_available, coa_available, concentration_percent
            FROM ingredients ORDER BY inci_name
        """, conn)
    return df

# Load products
@st.cache_data
def load_products():
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT name, category, is_clean_labeled FROM products ORDER BY name", conn)
    return df

def update_ingredient_details(ingredient_id, type_origin, complexity, source, sds, coa, concentration):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE ingredients
                SET type_origin = %s,
                    inci_complexity = %s,
                    source_info = %s,
                    sds_available = %s,
                    coa_available = %s,
                    concentration_percent = %s
                WHERE ingredient_id = %s
            """, (type_origin, complexity, source, sds, coa, concentration, ingredient_id))
            conn.commit()

# Smart INCI classifier
def classify_inci(inci):
    if any(x in inci.lower() for x in [",", "+"]) or any(char.isdigit() for char in inci):
        return 'complex'
    return 'simple'

# Streamlit UI
st.title("CosmIQ Dashboard")

# Section: Product Overview
st.subheader("Product Overview")
products_df = load_products()
st.dataframe(products_df)

# Visualizations
st.subheader("Product Category Distribution")
category_counts = products_df['category'].value_counts().reset_index()
category_counts.columns = ['Category', 'Count']
fig = px.bar(category_counts, x='Category', y='Count', title="Products per Category")
st.plotly_chart(fig)

clean_label_counts = products_df['is_clean_labeled'].value_counts().reset_index()
clean_label_counts.columns = ['Clean Labeled', 'Count']
fig2 = px.pie(clean_label_counts, names='Clean Labeled', values='Count', title="Clean Labeled Products")
st.plotly_chart(fig2)

# Section: Ingredient Type Origin
st.subheader("Ingredient List")
df = load_ingredients()
for idx, row in df.iterrows():
    with st.expander(f"{row['inci_name']} (Current: {row['type_origin'] if row['type_origin'] else 'Not set'})"):
        type_origin = st.radio("Type Origin:", ["raw", "compounded"], index=["raw", "compounded"].index(row['type_origin']) if row['type_origin'] else 0, key=f"type_{idx}")
        auto_complexity = classify_inci(row['inci_name'])
        st.markdown(f"**Auto INCI Complexity Suggestion:** `{auto_complexity}`")
        complexity = st.selectbox("INCI Complexity:", ["simple", "complex"], index=["simple", "complex"].index(row['inci_complexity']) if row['inci_complexity'] else ["simple", "complex"].index(auto_complexity), key=f"complexity_{idx}")
        source_info = st.text_input("Source Info:", value=row['source_info'] or "", key=f"source_{idx}")
        sds_available = st.radio("SDS Available:", [True, False], index=0 if row['sds_available'] else 1, key=f"sds_{idx}")
        coa_available = st.radio("COA Available:", [True, False], index=0 if row['coa_available'] else 1, key=f"coa_{idx}")
        concentration = st.number_input("Concentration (%):", value=row['concentration_percent'] if row['concentration_percent'] is not None else 0.0, min_value=0.0, max_value=100.0, key=f"conc_{idx}")
        if st.button("Update", key=f"btn_{idx}"):
            update_ingredient_details(row['ingredient_id'], type_origin, complexity, source_info, sds_available, coa_available, concentration)
            st.success(f"Updated details for '{row['inci_name']}'")
