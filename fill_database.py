import database as db
import csv

db.init_connection()



tables_insertions = {
    'offers' : [],
    'clients': [],
    'domains': [],
    'websites': [],
    'mailboxes': []
}

def insert_into_tables():
    for queries in tables_insertions.values():
        for q in queries:
            # print(q)
            db.query_with_commit(q)
        if (queries):
            print("Inserted values to table: " + queries[0].split(' ')[2])

# Offers
offers = '''INSERT INTO Offers VALUES 
    ('MAIL', 1024, 1024, 1, 0, 0),
    ('DUOMAIL', 2048, 2048, 2, 0, 0),
    ('MICRO', 1024, 1024, 1, 1, 1),
    ('MINI', 5120, 5120, 5, 5, 2),
    ('MINI+', 10240, 10240, 7, 7, 3),
    ('MEDIUM', 20480, 15360, 999, 999, 5),
    ('MAX', 51200, 51200, 999, 999, 999)'''

tables_insertions['offers'].append(offers)

def substring(table):
    return 'INSERT INTO {} VALUES '.format(table)

def add_parentheses(str):
    return '(' + str + ')'

def create_string_val(str):
    return "'" + str + "'"

def add_array_parentheses(str):
    return create_string_val('{' + str + '}') 



# Clients
def clients_insertion(row, id):
    clients_keys = ['name', 'offer', 'start_date', 'end_date', 'tax_id', 'phone_number', 'contact']
    
    row['contact'] = add_array_parentheses(row['contact'])
    row['phone_number'] = add_array_parentheses(row['phone_number'])
    for key in clients_keys[:4]:
        row[key] = create_string_val(row[key]) 
    
    insrt_val = substring('Clients') + add_parentheses(', '.join([id] + [row[k] if row[k] != '' else 'NULL' for k in clients_keys]))
    tables_insertions['clients'].append(insrt_val)

# Domains
def domains_insertion(row, id):
    domains = row['domains'].split(', ')
    for d in domains:
        if (d != ''):
            insrt_val = substring('Domains') + add_parentheses(', '.join([create_string_val(d), id]))
            tables_insertions['domains'].append(insrt_val)


# Mailboxes
cnt_emails = 1
def create_email_insertion(mailboxes, domain, id):
    global cnt_emails
    domain = create_string_val(domain)
    for m in mailboxes:
        if m[0] == '':
            break
        space = m[0]
        if m[1].count('@') > 0:
            name, domain = m[1].split('@')
            domain = create_string_val(domain)
        else:
            name = m[1]
        
        name = create_string_val(name)
        has_alias = 'FALSE'
        if name[1] == '>':
            name = "'" + name[2:]
            has_alias = 'TRUE'
        insert_val = substring('Mailboxes') + add_parentheses(', '.join([str(cnt_emails), name, space, id, has_alias, domain]))
        cnt_emails += 1
        tables_insertions['mailboxes'].append(insert_val)


def emails_insertion(row, id):
    mailboxes = row['mailboxes']
    if mailboxes == '':
        return

    if mailboxes[0] == '"':
        mailboxes = mailboxes[1:-1]
    
    if mailboxes[0].isdigit():
        mailboxes = [m.split(': ') for m in mailboxes.split(', ')] 
        create_email_insertion(mailboxes, row['domains'], id)
    else:
        various_domains_mailboxes = [m.split(' [') for m in mailboxes.split('@')[1:]]
        various_domains_mailboxes = [[m[0], [x.split(': ') for x in m[1][:-2].split(', ')]] for m in various_domains_mailboxes if m[1][:-2] != '']
        for domain, mails in various_domains_mailboxes:
            create_email_insertion(mails, domain, id)

# Websites
cnt_webs = 1
def websites_insertion(row, id):
    global cnt_webs
    websites = row['website'].split(', ')
    directories = row['points_at'].split(', ')
    if websites[0] == '':
        return

    for w, d in zip(websites, directories):
        w = create_string_val(w)
        d = create_string_val(d)
        insrt_value = substring('Websites') + add_parentheses(', '.join([str(cnt_webs), '0', id, w, d]))
        cnt_webs += 1
        tables_insertions['websites'].append(insrt_value)


with open('data.csv', encoding='utf-8-sig') as f:
    csvreader = csv.DictReader(f, delimiter=';')
    counter = 0
    for row in csvreader:
        counter += 1
        client_id = str(counter)
        clients_insertion(row, client_id)
        domains_insertion(row, client_id)
        emails_insertion(row, client_id)
        websites_insertion(row, client_id)

insert_into_tables()

db.close_connection()