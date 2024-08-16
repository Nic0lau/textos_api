import os
import sqlite3
from config import DB_FILENAME

if os.path.exists(DB_FILENAME):
    os.remove(DB_FILENAME)

con = sqlite3.connect(DB_FILENAME)
cur = con.cursor()

cur.execute("""
                CREATE TABLE Users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    pass VARCHAR(100) NOT NULL
                    )
            """)


cur.execute("""
                CREATE TABLE Poems(
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					user INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    author VARCHAR(75),
                    poem TEXT NOT NULL,
                    FOREIGN KEY (user) REFERENCES Users (id)
                    )
            """)

shakespeare = open("../shakespeare.txt", "r")

sonnets = []
current_sonnet = ""

for line in shakespeare:
    if line == "\n":
        sonnets.append(current_sonnet)
        current_sonnet = ""
        continue
    current_sonnet += line

data = []

for i in range(0, len(sonnets)):
    data.append((1, f"Sonnet {i+1}", "William Shakespeare", sonnets[i]))

cur.execute("INSERT INTO Users VALUES (NULL, '', '')")
cur.executemany("INSERT INTO Poems VALUES (NULL, ?, ?, ?, ?)", data)

con.commit()
con.close()
