import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="AviKedar@MySQL#11!",
    database="offer_letter_system"
)

if conn.is_connected():
    print("Database Connected Successfully!")