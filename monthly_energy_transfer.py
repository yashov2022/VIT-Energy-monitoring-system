import mysql.connector
from datetime import datetime, timedelta
import sys

# ==============================
# CONFIGURATION
# ==============================
DB_HOST = "HOST_DB_LIST"
DB_USER = "root"
DB_PASSWORD = " "

TABLE_NAME = "daily_energy_forecast"
ROWS_TO_COPY = 8  # ⚠️ Set equal to LSTM lookback window


# ==============================
# DETERMINE MONTH DATABASES
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
    print("Connecting to MySQL...")

    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )

    cursor = connection.cursor(dictionary=True)

    print("Connected successfully.")

    # ==============================
    # CREATE NEW DATABASE IF NOT EXISTS
    # ==============================
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {current_month_db}")
    print(f"Database {current_month_db} ensured.")

    # ==============================
    # CREATE TABLE STRUCTURE IF NOT EXISTS
    # ==============================
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {current_month_db}.{TABLE_NAME}
        LIKE {previous_month_db}.{TABLE_NAME}
    """)
    print("Table structure copied/verified.")

    # ==============================
    # FETCH LAST N ROWS
    # ==============================
    fetch_query = f"""
        SELECT *
        FROM {previous_month_db}.{TABLE_NAME}
        ORDER BY forecast_date DESC
        LIMIT {ROWS_TO_COPY}
    """

    cursor.execute(fetch_query)
    rows = cursor.fetchall()

    if not rows:
        print("No data found in previous database.")
        sys.exit(0)

    rows.reverse()  # Maintain chronological order

    print(f"Fetched {len(rows)} rows.")

    # ==============================
    # INSERT INTO NEW DATABASE
    # ==============================
    columns = rows[0].keys()
    column_names = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))

    insert_query = f"""
        INSERT IGNORE INTO {current_month_db}.{TABLE_NAME}
        ({column_names})
        VALUES ({placeholders})
    """

    for row in rows:
        cursor.execute(insert_query, tuple(row.values()))

    connection.commit()

    print(f"Inserted {len(rows)} rows into {current_month_db} successfully.")

except mysql.connector.Error as err:
    print("MySQL Error:", err)

except Exception as e:
    print("General Error:", e)

finally:
    if cursor is not None:
        cursor.close()

    if connection is not None and connection.is_connected():
        connection.close()
        print("MySQL connection closed.")