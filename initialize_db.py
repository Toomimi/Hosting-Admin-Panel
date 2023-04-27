import database as db;

db.init_connection()

tables = [
    '''CREATE TABLE Offers
    (
        name               VARCHAR(7) PRIMARY KEY,
        storage_limit      INT NOT NULL,
        mail_storage_limit INT NOT NULL, 
        mailboxes_limit    INT NOT NULL, 
        alias_limit        INT NOT NULL,
        databases_limit    INT NOT NULL
    ); ''',

    '''CREATE TABLE Clients
    (
        id           INT PRIMARY KEY,
        name         VARCHAR(100) NOT NULL,
        offer        VARCHAR(7) NOT NULL REFERENCES Offers ON DELETE RESTRICT,
        period_start DATE NOT NULL,
        period_end   DATE NOT NULL,
        tax_id       BIGINT,
        phone_number INT[],
        contact_mail VARCHAR(40)[] NOT NULL
    );''',

    '''CREATE TABLE Domains
    (
        name      VARCHAR(30) PRIMARY KEY,
        client_id INT NOT NULL REFERENCES Clients ON DELETE CASCADE
    );''',

    '''CREATE TABLE Websites
    (
        id             INT PRIMARY KEY,
        used_storage   INT NOT NULL,
        client_id      INT NOT NULL REFERENCES Clients ON DELETE CASCADE,
        website_domain VARCHAR(30) NOT NULL REFERENCES Domains ON DELETE CASCADE,
        directory_name VARCHAR(30) NOT NULL,
        UNIQUE(website_domain, directory_name)
    );''',

    '''CREATE TABLE Mailboxes
    (
        id            INT PRIMARY KEY,
        name          VARCHAR(30) NOT NULL,
        used_storage  INT NOT NULL ,
        client_id     INT NOT NULL REFERENCES Clients ON DELETE CASCADE,
        has_alias     BOOLEAN NOT NULL,
        email_domain  VARCHAR(30) NOT NULL REFERENCES Domains ON DELETE CASCADE
    ); '''
    
]

def create_tables():
    for table in tables:
        db.query_with_commit(table)
        print("Table: " + table.split(' ')[2][:-1] + " created successfully in PostgreSQL")


create_tables()

db.close_connection()