import psycopg
import pandas as pd

conn_str = (
    "postgresql://neondb_owner:npg_o0HsChQ4lkSa"
    "@ep-holy-unit-a5k4mdnx-pooler.us-east-2.aws.neon.tech/neondb"
    "?sslmode=require&options=endpoint%3Dep-holy-unit-a5k4mdnx-pooler"
)

with psycopg.connect(conn_str) as conn:
    for table in ["products", "brands", "ingredients"]:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        df.to_csv(f"{table}.csv", index=False)

