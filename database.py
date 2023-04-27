import streamlit as st
import psycopg2 as pg

conn = None

# @st.cache(allow_output_mutation=True, hash_funcs={"_thread.RLock": lambda _: None})
# @st.experimental_memo
def init_connection():
    global conn
    conn = pg.connect(**st.secrets["postgres"]) 

# Perform query.
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def query_with_commit(query):
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()

# Close connection
def close_connection():
    conn.close()