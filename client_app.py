import streamlit as st
import database as db
import pandas as pd
from forms import run_forms_app
from forms import get_limit
from forms import get_used_space

def home_page_button():
    if st.button('Strona Główna'):
        st.session_state['cl_id'] = 0
        st.session_state['form'] = 'home'
        st.session_state['clicked'] = False
        st.experimental_rerun()

def client_data_page_button():
    if st.button('Powrót'):
        st.session_state['form'] = 'home'
        st.session_state['clicked'] = False
        st.experimental_rerun()

@st.cache(ttl=600)
def get_offer_and_period(cl_q, cl_id):
    offer, beg, end = db.run_query(cl_q.format('offer, period_start, period_end', cl_id))[0]
        
    offer = offer[0] + offer[1:].lower()
    date = "{:%d.%m.%Y}"
    period = date.format(beg) + '-' + date.format(end)    
    return offer, period

@st.cache(ttl=300)
def get_client_data(cl_id, used_space):
    cl_q = "SELECT {} FROM Clients WHERE id = {}"
    q_res = list(db.run_query(cl_q.format('name, contact_mail, phone_number, tax_id', cl_id))[0])

    name = q_res[0]
    offer, period = get_offer_and_period(cl_q, cl_id)
    used = '{:.0f} MB'.format(used_space) 

    keys = ['Pakiet', 'okres', 'Wykorzystane miejsce', 'Mail kontaktowy', 'Telefon', 'NIP']
    res = [[offer], [period], [used]]
    for n in q_res[1:]:
        if type(n) == list:
            n = str(n)[1:-1].replace("'", '')
        if n is None or n == '':
            n = "Brak"
        if type(n) != str:
            n = str(n)    
        res.append([n])

    return name, pd.DataFrame(res, index=keys, columns=[''])

@st.cache(ttl=600)
def get_domains(cl_id, webs_size):
    q = ''' SELECT name, directory_name, used_storage, CASE WHEN cnt is NULL THEN 0 ELSE cnt END
         FROM 
            (SELECT name, directory_name, used_storage 
                    FROM Domains D LEFT JOIN Websites W ON D.name = W.website_domain WHERE D.client_id = {id}) A 
            LEFT JOIN 
            (SELECT email_domain, count(*) AS cnt FROM Mailboxes WHERE client_id = {id} GROUP BY email_domain) B
            ON A.name = B.email_domain ORDER BY name'''.format(id=cl_id)   
    
    q_res = db.run_query(q)
    mailboxes_count = 0
    res = []
    for row in q_res:
        new_row = []
        for col in row:
            if col is None:
                col = 'Brak'
            if len(new_row) == 2 and col != 'Brak':
                col = '{} MB'.format(col)
            if len(new_row) == 3:
                mailboxes_count += col
            new_row.append(col)
        res.append(new_row)
    res.append(['', '', '{} MB'.format(webs_size), mailboxes_count])

    clmns = ['Domena', 'Wskazuje na katalog', 'Rozmiar Katalogu', 'Liczba skrzynek']
    df = pd.DataFrame(res, columns=clmns)

    df_len = len(df)
    ind = [str(i) for i in range(1, df_len)] 
    ind.append('Razem:')
    df.index = ind

    return df, len(res) - 1

@st.cache(ttl=600)
def get_mailboxes(cl_id, mails_size):
    q = "SELECT name, email_domain, has_alias, used_storage FROM Mailboxes WHERE client_id = {}".format(cl_id)
    q_res = db.run_query(q)
    
    aliases_cnt = 0
    res = []
    for row in q_res:
        new_row = ['@'.join(row[:2])]
        for col in row[2:]:
            if col == True:
                col = 'Tak'
                aliases_cnt += 1
            if col == False:
                col = 'Nie'
            if len(new_row) == 2:
                col = '{} MB'.format(col)
            new_row.append(col)
        res.append(new_row)
    res.append(['', str(aliases_cnt), '{} MB'.format(mails_size)])
    
    clmns = ['Nazwa', 'Alias', 'Rozmiar']
    df = pd.DataFrame(res, columns=clmns)
    
    df_len = len(df)
    ind = [str(i) for i in range(1, df_len)] 
    ind.append('Razem:')
    df.index = ind
    
    return df

def align_button(domain_cnt):
    spaces = {0: 0, 1: 0, 2: 1, 3: 3, 4: 4, 5: 5, 6: 7, 7: 9, 8: 10}
    for _ in range(spaces.get(domain_cnt, 10)):
        st.text('')

def client_data_forms_buttons(domains_expand, mailboxes_expand, domain_cnt):
    if st.button('Dodaj Domenę'):
        st.session_state['form'] = 'add_domain'
        st.experimental_rerun()
    if domains_expand:
        if st.button("Edytuj domenę"):
            st.session_state['form'] = 'edit_domain'
            st.experimental_rerun()
        if st.button("Usuń domenę"):
            st.session_state['form'] = 'remove_domain' 
            st.experimental_rerun()
        align_button(domain_cnt)
    if st.button('Dodaj skrzynkę'):
        st.session_state['form'] = 'add_mailbox'
        st.experimental_rerun()
    if mailboxes_expand:
        if st.button("Edytuj skrzynkę"):
            st.session_state['form'] = 'edit_mailbox'
            st.experimental_rerun()
        if st.button("Usuń skrzynkę"):
            st.session_state['form'] = 'remove_mailbox'
            st.experimental_rerun()

def client_data_app(cl_id):
    home_page_button()
    
    mails_size, webs_size = get_used_space(cl_id)    
    name, df = get_client_data(cl_id, mails_size + webs_size)
    
    st.title(name)
    col1, col2, col3, col4 = st.columns([1, 2, 0.5, 0.5])
    with col1:
        st.dataframe(df)

        sum = (mails_size + webs_size)
        used_prcntg = sum / get_limit(cl_id)
        st.markdown('<p class="right"><b> {}/{} MB</p></b>'.format(sum, get_limit(cl_id)), unsafe_allow_html=True)
        used_prcntg = used_prcntg if used_prcntg < 1 else 100
        st.progress(used_prcntg)
    with col2:
        dm_cnt = 0
        domains = st.checkbox('Pokaż domeny')
        if domains:
            dm_df, dm_cnt = get_domains(cl_id, webs_size)
            st.dataframe(dm_df)
        mailboxes = st.checkbox('Pokaż skrzynki')
        if mailboxes:
            st.dataframe(get_mailboxes(cl_id, mails_size))
    with col3:
        client_data_forms_buttons(domains, mailboxes, dm_cnt)
        
def run_client_app():
    if 'form' not in st.session_state:
        st.session_state['form'] = 'home'

    cl_id = st.session_state['cl_id']
    
    if st.session_state['form'] == 'home':
       client_data_app(cl_id)
    else:
        c1, c2, c3 = st.columns([1, 1, 10])
        with c1:
            home_page_button()
        with c2:
            client_data_page_button()
        run_forms_app(cl_id)