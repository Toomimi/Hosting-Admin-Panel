from copy import deepcopy
from this import d
from time import sleep
from string import whitespace
import database as db
import streamlit as st


def back_to_client_data_app():
    sleep(0.7)
    st.session_state['form'] = 'home'
    st.session_state['clicked'] = False
    st.legacy_caching.caching.clear_cache()
    st.experimental_rerun()

def get_sizes():
    sizes = ['500 MB', '1000 MB', '50 MB', '100 MB', '200 MB', '300 MB',
         '400 MB', '750 MB', '1500 MB', '2000 MB', '3000 MB', '5000 MB']
    return sizes

def invalid_name(name):
    invalid = r'''!@#$%^&*'()"/><|\{}][+_-=,:;''' + whitespace
    return name == '' or any(el in name for el in invalid)

def next_id(table):
    q = "SELECT MAX(id) FROM {}".format(table)
    return db.run_query(q)[0][0] + 1

@st.cache(ttl=600)
def get_website_id(domain, directory):
    q = "SELECT id FROM Websites WHERE website_domain = '{}' and directory_name = '{}'"
    q_res = db.run_query(q.format(domain, directory))
    if len(q_res) == 0:
        return -1
    return q_res[0][0]

@st.cache(ttl=600)
def get_all_domains():
    q = 'SELECT name FROM Domains'
    q_res = db.run_query(q)
    all_domains = []
    for d in q_res:
        all_domains.append(d[0])
    return all_domains

@st.cache(ttl=600)
def get_mailbox_data(name, domain):
    q = '''SELECT used_storage, has_alias, id FROM Mailboxes
         WHERE email_domain = '{}' and name = '{}' '''    
    q_res = db.run_query(q.format(domain, name))[0]
    return q_res[0], q_res[1], q_res[2]
    
@st.cache(ttl=600)
def get_limit(cl_id):
    q = '''SELECT storage_limit FROM Offers 
        WHERE name IN (SELECT Offer FROM Clients WHERE id = {})'''.format(cl_id)
    return db.run_query(q)[0][0]

@st.cache(ttl=600)
def get_client_domains_list(cl_id, with_mailboxes=False):
    q = 'SELECT D.name FROM Domains D WHERE client_id = {}'.format(cl_id)
    if with_mailboxes:
        q += 'AND D.name in (SELECT email_domain FROM Mailboxes where email_domain = D.name)'
    q_res = db.run_query(q)
    domains = []
    for d in q_res:
        domains.append(d[0])
    return domains

@st.cache(ttl=300)
def get_used_space(cl_id):
    used_mails_q = "SELECT SUM(used_storage) FROM Mailboxes WHERE client_id = {}".format(cl_id)
    used_webs_q = '''SELECT SUM(us) FROM (SELECT MAX(used_storage) AS us 
                FROM Websites where client_id = {} GROUP BY directory_name) A'''.format(cl_id)

    mails_size = db.run_query(used_mails_q)[0][0]
    webs_size = db.run_query(used_webs_q)[0][0]
    webs_size = webs_size if webs_size is not None else 0
    mails_size = mails_size if mails_size is not None else 0
    return mails_size, webs_size

@st.cache(ttl=600)
def get_domain_mailboxes(chosen_domain):
    q = "SELECT name FROM Mailboxes where email_domain = '{}'".format(chosen_domain)
    q_res = db.run_query(q)
    names = []
    for n in q_res:
        names.append(n[0])
    return names

@st.cache(ttl=600)
def get_directory_size(dir):
    q = "SELECT used_storage FROM Websites WHERE directory_name = '{}'".format(dir)
    q_res = db.run_query(q)
    if len(q_res) == 0:
        return 0
    return q_res[0][0]

@st.cache(ttl=600)
def get_pointed_directory(domain):
    q = "SELECT directory_name FROM Websites WHERE website_domain = '{}'"
    q_res = db.run_query(q.format(domain))
    if len(q_res) == 0:
        return 'Brak'
    return q_res[0][0]

def verify_new_mailbox(name, chosen_domain, cl_id, chosen_size,
                                    prefix='', check_duplicate=True):
    if invalid_name(name):
        st.warning(prefix + "Niewłaściwa nazwa.")
        return False
    if check_duplicate and name in get_domain_mailboxes(chosen_domain):
        st.warning(prefix + "Nazwa już istnieje.")
        return False
    if get_limit(cl_id) < int(chosen_size) + get_used_space(cl_id)[0]:
        st.warning(prefix + "Wybrany rozmiar przekracza limit pakietu.")
        return False
    return True

def verify_new_domain(name, check_duplicate=True):
    if invalid_name(name):
        st.warning('Niewłaściwa nazwa.')
        return False
    if check_duplicate and name in get_all_domains():
        st.warning('Domena już istnieje.')
        return False
    return True

def invalid_domain_delete(domain):
    q = "SELECT id FROM Mailboxes WHERE email_domain = '{}'".format(domain)
    q_res = db.run_query(q)
    if len(q_res) > 0:
        st.warning('''Nie można usunąć domeny, ponieważ istnieją przypisane do niej skrzynki.
         Wybierz inną domenę lub najpierw usuń wszystkie przypisane skrzynki.''')
        return True
    return False

def remove_form(warning_msg, query1, with_domain_check=False, dmn=''):
    if 'clicked' not in st.session_state:
        st.session_state['clicked'] = False

    container = st.container()
    with st.empty():
        if st.button("Usuń"):
            st.text("")
            st.session_state['clicked'] = True

    if st.session_state['clicked'] and with_domain_check and invalid_domain_delete(dmn):
        st.session_state['clicked'] = False

    if st.session_state['clicked']:
        c1,c2,c3 = st.columns([10, 1, 1])
        container.warning(warning_msg)
        with c1:
            st.text(' ')
        with c2:
            if st.button('Potwierdź'):
                db.query_with_commit(query1)
        
                container.success("Usunięto")
                back_to_client_data_app()
        with c3:
            if st.button('Anuluj'):
                st.session_state['clicked'] = False
                st.experimental_rerun()

def streamlit_mailbox_form(domains, submit_button, name_txt='',
                                 sizes=get_sizes(), alias_checked=False):
    with st.form("add_or_edit_mailbox"):
        name = st.text_input("Nazwa skrzynki", name_txt)
        domain = st.selectbox("Domena", domains)
        size = st.selectbox("Rozmiar", sizes)[:-2]
        alias = st.checkbox("Alias", value=alias_checked)
        submit = st.form_submit_button(submit_button)
    return name, domain, size, alias, submit

def add_mailbox_form(cl_id):
    domains = get_client_domains_list(cl_id)    
    form_val = streamlit_mailbox_form(domains, 'Dodaj')
    name, chosen_dm, chosen_size, alias, submit = form_val

    if submit and verify_new_mailbox(name, chosen_dm, cl_id, chosen_size):
        new_mailbox_id = next_id('Mailboxes')
        insert_q = "INSERT INTO Mailboxes VALUES ({t[0]}, '{t[1]}', {t[2]}, {t[3]}, {t[4]}, '{t[5]}')"
        val = (new_mailbox_id, name, chosen_size, cl_id, alias, chosen_dm)
        db.query_with_commit(insert_q.format(t=val))
        
        st.success('Dodano')
        back_to_client_data_app()

def mailbox_choose_domain_and_name(cl_id):
    domains = get_client_domains_list(cl_id, with_mailboxes=True)
    dmn = st.selectbox("Wybierz domenę", domains)
    names = get_domain_mailboxes(dmn)
    name = st.selectbox("Wybierz skrzynkę", names)
    return name, dmn

def edit_mailbox_form(cl_id):
    name, dmn = mailbox_choose_domain_and_name(cl_id)
    size, alias, mailbox_id = get_mailbox_data(name, dmn)
    
    if 'clicked' not in st.session_state:
        st.session_state['clicked'] = False

    with st.empty():
        if st.button("Wybierz"):
            st.session_state['clicked'] = True
            st.text('')

    if st.session_state['clicked']:
        sizes = get_sizes()
        sizes.insert(0, sizes.pop(sizes.index(f'{size} MB')))
        domains = deepcopy(get_client_domains_list(cl_id))
        domains.insert(0, domains.pop(domains.index(dmn)))
        form_val = streamlit_mailbox_form(domains, 'Zmień', name, sizes, alias)
        new_name, dmn, new_size, alias, submit = form_val

        if submit and verify_new_mailbox(new_name, dmn, cl_id, int(new_size) - size,
                        "Nie dokonano zmian. ", check_duplicate=(new_name != name)):
            tup = (new_name, dmn, new_size, alias, mailbox_id)
            q = '''UPDATE Mailboxes SET name = '{t[0]}', email_domain = '{t[1]}',
             used_storage = {t[2]}, has_alias = {t[3]} WHERE id = {t[4]}'''
            q = q.format(t=tup)
            db.query_with_commit(q)
            st.success("Zmieniono")
            back_to_client_data_app()
        
def remove_mailbox_form(cl_id):
    name, dmn = mailbox_choose_domain_and_name(cl_id)
    warning_message = "Czy na pewno chcesz usunąć skrzynkę {}@{}?".format(name, dmn)
    query = "DELETE FROM Mailboxes WHERE email_domain = '{}' AND name = '{}'"
    query = query.format(dmn, name)
    remove_form(warning_message, query)

def add_domain_form(cl_id):
    with st.form('domain_form'):
        new_dm = st.text_input("Domena")
        points_at = st.text_input("Wskazuje na folder", 'Brak')
        submit = st.form_submit_button('Dodaj')
    
    if submit and verify_new_domain(new_dm):
        q_domain = "INSERT INTO Domains VALUES ('{}', {})".format(new_dm, cl_id)
        db.query_with_commit(q_domain)

        if points_at != 'Brak':
            size = get_directory_size(points_at)
            new_web_id = next_id('Websites')
            q_web = "INSERT INTO Websites VALUES ({}, {}, {}, '{}', '{}')"
            q_web = q_web.format(new_web_id, size, cl_id, new_dm, points_at)
            db.query_with_commit(q_web)
        
        st.success('Dodano')
        back_to_client_data_app()

def update_domain(dir, dmn, new_dir, new_dmn, cl_id):
    # web_id equals -1, when (dmn, dir) not in 'Websites'
    web_id = get_website_id(dmn, dir)
        
    q_up_dmn_dmns = "UPDATE Domains SET name = '{}' WHERE name = '{}'".format(new_dmn, dmn)
    db.query_with_commit(q_up_dmn_dmns)
    
    q = 'SELECT 1'

    if dir == new_dir and dir != 'Brak':
        q = "UPDATE Websites SET website_domain = '{}' WHERE id = {}".format(new_dmn, web_id)
    elif dir != new_dir:
        new_size = get_directory_size(new_dir)
        if new_dir == 'Brak':
            q = "DELETE FROM Websites WHERE id = {}".format(web_id)
        elif dir == 'Brak':
            q = "INSERT INTO Websites VALUES ({t[0]}, {t[1]}, {t[2]}, '{t[3]}', '{t[4]}')"
            tup = (next_id('Websites'), new_size, cl_id, new_dmn, new_dir)
            q = q.format(t=tup)
        else:
            q = '''UPDATE Websites SET website_domain = '{}', 
                used_storage = {}, directory_name = '{}' WHERE id = {}'''
            q = q.format(new_dmn, new_size, new_dir, web_id)
    db.query_with_commit(q)


def edit_domain_form(cl_id):
    domains = get_client_domains_list(cl_id)
    dmn = st.selectbox('Domena', domains)
    
    if 'clicked' not in st.session_state:
        st.session_state['clicked'] = False

    with st.empty():
        if st.button("Wybierz"):
            st.session_state['clicked'] = True
            st.text('')

    if st.session_state['clicked']:
        dir = get_pointed_directory(dmn)
        with st.form("domain_form"):
            new_dmn = st.text_input("Domena", dmn)
            new_dir = st.text_input("Wskazuje na folder", dir)
            new_dir = new_dir if not any(el in new_dir for el in whitespace) else 'Brak' 
            submit = st.form_submit_button("Zmień")
        
        if submit and verify_new_domain(new_dmn, check_duplicate=(dmn != new_dmn)):
            update_domain(dir, dmn, new_dir, new_dmn, cl_id)
            st.success('Zmieniono')
            back_to_client_data_app()

def remove_domain_form(cl_id):
    domains = get_client_domains_list(cl_id)
    to_delete = st.selectbox("Wybierz domenę do usunięcia", domains)
    
    warning_msg = '''Czy na pewno chcesz usunąć domenę {} 
            i wszystkie powiązane z nią strony?'''.format(to_delete)
    q = "DELETE FROM Domains WHERE name = '{}'".format(to_delete)
    remove_form(warning_msg, q, with_domain_check=True, dmn=to_delete)

def run_forms_app(cl_id):
    form_to_show = st.session_state['form']
    if form_to_show == 'add_mailbox':
        add_mailbox_form(cl_id)
    elif form_to_show == 'edit_mailbox':
        edit_mailbox_form(cl_id)
    elif form_to_show == 'remove_mailbox':
        remove_mailbox_form(cl_id)
    elif form_to_show == 'add_domain':
        add_domain_form(cl_id)
    elif form_to_show == 'edit_domain':
        edit_domain_form(cl_id)
    elif form_to_show == 'remove_domain':
        remove_domain_form(cl_id)
    else:
        st.warning("Page not found")
