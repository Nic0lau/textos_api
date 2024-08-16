import sqlite3
from config import DB_FILENAME

con = sqlite3.connect(DB_FILENAME)
cur = con.cursor()

for row in cur.execute("SELECT * FROM Users ORDER BY id ASC"):
    print(row)

con.close()
