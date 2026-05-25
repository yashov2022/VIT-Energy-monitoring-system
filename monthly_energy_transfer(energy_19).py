import mysql.connector
from datetime import datetime, timedelta
import sys

# ==============================
# CONFIGURATION
# ==============================
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""

TABLE_NAME = "energy_19"
ROWS_TO_COPY = 20   # match LSTM lookback


# ==============================
# DETERMINE DATABASE NAMES
# ==============================
today = datetime.today()

current_month_db = today.strftime("%m%Y")
previous_month_date = today.replace(day=1) - timedelta(days=1)
previous_month_db = previous_month_date.strftime("%m%Y")

print(f"Previous DB: {previous_month_db}")
print(f"Current DB: {current_month_db}")

connection = None
cursor = None

try:
    print("Connecting to MariaDB...")

    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )

    cursor = connection.cursor(dictionary=True)

    print("Connected successfully.")

    # ==============================
    # CREATE NEW DATABASE
    # ==============================
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{current_month_db}`")
    print("Database ensured.")

    # ==============================
    # CREATE TABLE STRUCTURE
    # ==============================
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS `{current_month_db}`.`{TABLE_NAME}`
        LIKE `{previous_month_db}`.`{TABLE_NAME}`
    """)
    print("Table structure ensured.")

    # ==============================
    # FETCH LAST N ROWS
    # ==============================
    fetch_query = f"""
        SELECT *
        FROM `{previous_month_db}`.`{TABLE_NAME}`
        ORDER BY day_date DESC
        LIMIT {ROWS_TO_COPY}
    """

    cursor.execute(fetch_query)
    rows = cursor.fetchall()

    if not rows:
        print("No data found in previous DB.")
        sys.exit(0)

    rows.reverse()

    print(f"Fetched {len(rows)} rows.")

    # ==============================
    # INSERT INTO NEW DB
    # ==============================
    columns = rows[0].keys()
    column_names = ", ".join([f"`{col}`" for col in columns])
    placeholders = ", ".join(["%s"] * len(columns))

    insert_query = f"""
        INSERT IGNORE INTO `{current_month_db}`.`{TABLE_NAME}`
        ({column_names})
        VALUES ({placeholders})
    """

    for row in rows:
        cursor.execute(insert_query, tuple(row.values()))

    connection.commit()

    print("Data transfer completed successfully.")

except mysql.connector.Error as err:
    print("MySQL Error:", err)

except Exception as e:
    print("General Error:", e)

finally:
    if cursor is not None:
        cursor.close()

    if connection is not None and connection.is_connected():
        connection.close()
        print("Connection closed.")