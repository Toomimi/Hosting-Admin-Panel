#!/usr/bin/env python3
import email.message
import smtplib
import subprocess

from numpy import size
import postgresql as pg


def send_email(body, subject, recipent = 'hosting@softbyte.pl'):
    message = email.message.EmailMessage()
    message["From"] = 'automat@softbyte.pl'
    message["To"] = recipent
    message["Subject"] = subject
    message.set_content(body)
    
    #Połączenie z serwerem i wysłanie wiadomości
    mail_server = smtplib.SMTP_SSL('gronet.home.pl')
    mail_server.login("automat@softbyte.pl", "Autom@t20")
    mail_server.send_message(message)
    mail_server.quit()

def send_over_limit_notification(tuple):
    subject = '[A] Przekroczenie limitu miejsca! [{t[0]}]'.format(t=tuple)
    body  = '''
{t[0]} przekracza limit swojego pakietu o {t[2]:.2f} GB.\n
Pakiet: {t[1]}
Wykorzystane miejsce: {t[5]} MB
  -skrzynki pocztowe: {t[3]} MB
  -strony internetowe: {t[4]} MB
'''.format(t=tuple)
    send_email(body, subject)

def send_folder_does_not_exist_notification(path):
    subject = '[A] Brak wskazywanego folderu'
    body = f'Folder o ścieżce {path} nie istnieje.'
    send_email(body, subject)

# directory disk usage
def du(path):
    try:
        output = subprocess.check_output(['du', '-sm', path])
    except:
        send_folder_does_not_exist_notification(path)
        return -1
    return output.split()[0].decode('utf-8')

db = pg.open('pq://10387911_bd:fs6vU.yc:wSy@localhost:5432/10387911_bd')
# db = pg.open('pq://10387911_bd:fs6vU.yc:wSy@gronet.home.pl:5432/10387911_bd')
query = db.prepare("SELECT used_storage AS us, directory_name AS dn FROM Websites")

directories_size = {}
with db.xact():
    for row in query():
        directories_size[row['dn']] = row['us']


def check_for_usage_updates():
    directories_to_update = []
    for dir in directories_size.keys():
        new = float(du('./' + dir))
        if new != directories_size[dir]:
            directories_size[dir] = new
            directories_to_update.append(dir)
    return directories_to_update

def update(dir):
    update_query = db.prepare('UPDATE Websites SET used_storage = $1 WHERE directory_name = $2')
    with db.xact():
            update_query(directories_size[dir], dir)

# Query returning Client_id, used_space (webs + mails)
clients_space_usage_query = '''
    (SELECT W.client_id, sumW, CASE
                                WHEN sumM is NULL THEN 0
                                ELSE sumM
                                END AS sumM
    FROM 
        (SELECT T.client_id, sum(used) AS sumW 
        FROM 
            (SELECT client_id, MAX(used_storage) AS used FROM Websites GROUP BY client_id, directory_name) T
        GROUP BY T.client_id) W
    LEFT JOIN 
        (SELECT client_id, sum(used_storage) AS sumM FROM Mailboxes GROUP BY client_id) M USING(client_id))'''

clients_limits_query = ''' (SELECT id AS client_id, C.name, offer, storage_limit FROM
                            Clients C JOIN Offers O ON C.offer = O.name)'''

# Query returning name, offer, storage_limit, webs_space_usage, mails_space_usage.
# For clients over their limit
clients_over_limit_query = '''
    SELECT name, offer, storage_limit, sumW, sumM FROM {} U JOIN {} Cl USING(client_id) 
    WHERE storage_limit < sumM + sumW'''.format(clients_space_usage_query, clients_limits_query )

clients_over_limit = db.prepare(clients_over_limit_query)


def update_and_check_limits_for_all(updated):
    over_limit = []
    for dir in updated:
        update(dir)

    with db.xact():
        for c in clients_over_limit():
            sumM = c['summ']
            sumW = c['sumw']
            usage = sumM + sumW
            limit = c['storage_limit']
            t = (c['name'], c['offer'], (usage - limit) / 1024, sumM, sumW, usage)
            over_limit.append(t)
    return over_limit


client_id = db.prepare("SELECT client_id FROM Websites WHERE directory_name = $1")
client_limit = db.prepare("SELECT C.name, offer, storage_limit FROM Clients C JOIN Offers O ON C.offer = O.name WHERE id = $1")
client_webs_usage = db.prepare("SELECT SUM(used) AS sum FROM (SELECT MAX(used_storage) AS used FROM Websites WHERE client_id = $1 GROUP BY directory_name) T")
client_mails_usage = db.prepare("SELECT SUM(used_storage) AS sum FROM Mailboxes WHERE client_id = $1")
     
def update_and_check_limits_for_updated(updated):
    over_limit = []
    for dir in updated:
        update(dir)
        with db.xact():
            id = client_id(dir)[0]['client_id']
            name, offer, limit = client_limit(id)[0]
            mails_q = client_mails_usage(id)[0]['sum'] 
            mails_usage = mails_q if mails_q is not None else 0
            webs_usage = client_webs_usage(id)[0]['sum'] 
            usage = mails_usage + webs_usage
        if (usage > limit):  
            t = (name, offer, (usage - limit) / 1024, mails_usage, webs_usage, usage)
            over_limit.append(t)
    return over_limit


def send_notifications_to_admin(over_limit):
    for client in over_limit:
        send_over_limit_notification(client)

if __name__ == "__main__":
    print("Checking size of directories..")
    directories_to_update = check_for_usage_updates()
    
    if not directories_to_update:
        print("Directories size didn't change, quiting.")
        quit()
    
    print("Updating sizes in database, and checking limits..")
    over_limit = update_and_check_limits_for_updated(directories_to_update)
    # over_limit = update_and_check_limits_for_all(directories_to_update)
    
    if not over_limit:
        print("No limits exceeded, quiting.")
        quit()
    
    print("Sending notifications..")
    send_notifications_to_admin(over_limit)
    print("Notifications sent, quting.")
