import streamlit as st
import pandas as pd
import numpy as np
import database as db
import time
from client_app import run_client_app 



st.set_page_config(
   page_title="Panel Hosting",
   layout="wide",
   initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.right {
    text-align: right;
} </style>
""", unsafe_allow_html=True)
st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)


def choose_client():
    st.session_state['cl_id'] = 0
    st.subheader('Wybierz klienta, żeby poznać jego szczegóły')
    def get_clients():
        client_ids = {'wybierz' : 0}
        for cl in db.run_query('SELECT name, id FROM Clients'):
            client_ids[cl[0]] = cl[1]
        return client_ids

    def get_domains():
        domains_ids = {'wybierz' : 0}
        for d in db.run_query('SELECT name, client_id FROM Domains'):
            domains_ids[d[0]] = d[1]
        return domains_ids
    
    search_by = st.selectbox( 'Szukaj po:', ['Domenie', 'Nazwie'])

    if search_by == 'Nazwie':
        clients_ids = get_clients()
        cl_id = clients_ids[st.selectbox('Wybierz nazwę:', clients_ids.keys())]
    else:
        clients_domains = get_domains()
        cl_id = clients_domains[st.selectbox('Wybierz domenę:', clients_domains.keys())]
    
    if (cl_id != 0):
        st.session_state['cl_id'] = cl_id
        st.experimental_rerun()

def main():
    
    if 'cl_id' not in st.session_state:
        st.session_state['cl_id'] = 0
    
    if st.session_state['cl_id'] == 0: 
        choose_client()
    else:
        run_client_app()


if __name__ == "__main__":    
    
    db.init_connection()

    main()

    # close the communication with the PostgreSQL
    db.close_connection()
