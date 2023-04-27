# Hosting Admin Panel

This is web app, which can be hosted on any machine able to launch with Streamlit library for python. It connects to postgress database located on a server.

### Files:

- Database files:
  - initialize_db,py: Initializes database
  - fill_database.py: Fills created database with data from data.csv (not included in repository)
  - database.py: Utils for queries to database.
- Server files:
  - cron.py: File which is located on server and check websites directories size
- App files: 
  - first.py
  - forms.py
  - client_app.py

### Run app:
streamlit run first.py
(Database connection credentials need to be filled) 