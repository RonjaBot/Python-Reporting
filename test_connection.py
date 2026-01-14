import pg8000

conn = pg8000.connect(
    host="localhost",
    database="pagila_dwh",
    user="postgres",
    password="hello1234",
    port=5432,
)

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM vw_rental_analysis")
print("Total records:", cur.fetchone()[0])

conn.close()
