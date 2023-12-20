import psycopg2

def get_db_connection():
    connection = psycopg2.connect(
        host='db-cc.co4twflu4ebv.us-east-1.rds.amazonaws.com',
        port=5432,
        user='master',
        password='MasterPassword',
        database='lion_leftovers'
    )
    return connection

try:
    conn = get_db_connection()
    print("Successfully connected to the database")
    # Optionally, you can perform a simple query here
    cursor = conn.cursor()
    cursor.execute("SELECT 1")  # Simple query
    print("Query executed successfully:", cursor.fetchone())
    cursor.close()
except Exception as e:
    print("Error while connecting to the database:", e)
finally:
    if conn is not None:
        conn.close()
        print("Database connection closed")