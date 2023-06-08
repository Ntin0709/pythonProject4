import sqlite3

# Create a SQLite database and connect to it
conn = sqlite3.connect('your_database.db')
cursor = conn.cursor()

# Create the parties table
cursor.execute('''CREATE TABLE parties
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   party_name TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY,
                party_name TEXT NOT NULL,
                bill_no TEXT NOT NULL,
                total_amount REAL,
                remaining_amount REAL,
                paid_status INTEGER DEFAULT 0,
                paid_date TEXT,
                UNIQUE(party_name, bill_no)
            )''')

# Create the "items" table
cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                bill_id INTEGER,
                sr_no INTEGER,
                item_name TEXT,
                description_image TEXT,
                description_text TEXT,
                meters REAL,
                rate REAL,
                total REAL,
                FOREIGN KEY(bill_id) REFERENCES bills(id)
            )''')
# Insert dummy data into the parties table
# parties_data = [
#     ('Party 1'),
#     ('Party 2'),
#     ('Party 3')
# ]

# cursor.executemany("INSERT INTO parties (party_name) VALUES (?)", parties_data)

# # Get the last inserted party id
# last_party_id = cursor.lastrowid
conn.commit()
conn.close()

print("Database created and dummy data inserted successfully.")
