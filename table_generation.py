import mysql.connector
from datetime import datetime
import logging

# ================== CONFIG ==================
HOST = "localhost"
USER = "root"
PASSWORD = ""
# ============================================

# 🔹 LOGGING
logging.basicConfig(
    filename="db_creation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_current_db():
    return datetime.now().strftime("%m%Y")

def get_next_month_db():
    now = datetime.now()
    month = now.month
    year = now.year

    if month == 12:
        return f"01{year+1}"
    else:
        return f"{month+1:02d}{year}"

try:
    CURRENT_DB = get_current_db()
    NEXT_DB = get_next_month_db()

    print(f"Current DB: {CURRENT_DB}")
    print(f"Next DB: {NEXT_DB}")

    conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD
    )
    cursor = conn.cursor()

    # 🔹 CHECK CURRENT DB
    cursor.execute(f"SHOW DATABASES LIKE '{CURRENT_DB}'")
    if not cursor.fetchone():
        raise Exception(f"❌ Current DB `{CURRENT_DB}` not found!")

    # 🔹 CREATE NEXT DB IF NOT EXISTS (no skipping now)
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{NEXT_DB}`")
    print(f"✅ Database `{NEXT_DB}` ready")

    # 🔹 GET TABLES FROM CURRENT DB
    cursor.execute(f"SHOW TABLES FROM `{CURRENT_DB}`")
    tables = cursor.fetchall()

    if not tables:
        raise Exception(f"❌ No tables found in `{CURRENT_DB}`")

    # 🔹 CREATE TABLES (IMPORTANT CHANGE: IF NOT EXISTS)
    for (table_name,) in tables:
        print(f"Ensuring table: {table_name}")

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{NEXT_DB}`.`{table_name}`
            LIKE `{CURRENT_DB}`.`{table_name}`
        """)

    conn.commit()

    print("🎉 Tables ensured successfully!")
    logging.info(f"SUCCESS: Ensured tables in {NEXT_DB}")

except Exception as e:
    print("❌ ERROR:", e)
    logging.error(f"ERROR: {str(e)}")

finally:
    try:
        cursor.close()
        conn.close()
    except:
        pass