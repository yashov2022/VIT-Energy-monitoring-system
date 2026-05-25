import mysql.connector
from datetime import datetime, timedelta
import logging
import os
import sys

# --------------------------------------------------
# 🔹 DATABASE CONFIG
# --------------------------------------------------

HOST = "localhost"
USER = "root"
PASS = ""

try:
    # Yesterday date
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')
    yesterday_date = datetime.now().date() - timedelta(days=1)

    logging.info(f"Yesterday string: {yesterday_str}")

    conn = mysql.connector.connect(host=HOST, user=USER, password=PASS)
    cursor = conn.cursor()

    # --------------------------------------------------
    # 🔎 Find Monthly Database
    # --------------------------------------------------

    cursor.execute("SHOW DATABASES")
    dbs = [d[0] for d in cursor.fetchall()]

    month = datetime.now().month
    year = datetime.now().year

    db_name = None
    for db in dbs:
        if db.isdigit() and int(db[:2]) == month and int(db[2:]) == year:
            db_name = db

    if db_name is None:
        logging.error("Monthly DB not found")
        sys.exit()

    logging.info(f"Selected DB: {db_name}")

    conn.database = db_name

    table = "meitest19"   # 🔁 Change for other buildings

    # --------------------------------------------------
    # 🔹 FETCH FULL DAY STATISTICS
    # --------------------------------------------------

    query = f"""
        SELECT
        ABS
        (
            (
                SELECT RealEnergyWH
                FROM {table}
                WHERE Datetime LIKE %s
                ORDER BY Datetime ASC
                LIMIT 1
            )
            -
            (
                SELECT RealEnergyWH
                FROM {table}
                WHERE Datetime LIKE %s
                ORDER BY Datetime DESC
                LIMIT 1
            )
            ),

            AVG(LineVoltageVRY), AVG(LineVoltageVYB), AVG(LineVoltageVBR),

            AVG(PhaseVoltageVRN), AVG(PhaseVoltageVYN), AVG(PhaseVoltageVBN),

            AVG(LineCurrentIR), AVG(LineCurrentIY), AVG(LineCurrentIB),

            AVG(PowerFactor),
            AVG(Frequency)

        FROM {table}
        WHERE Datetime LIKE %s
    """

    cursor.execute(query, (
        yesterday_str + "%",   # start value
        yesterday_str + "%",   # end value
        yesterday_str + "%"    # avg calculations
    ))

    row = cursor.fetchone()

    if row is None or row[0] is None:
        logging.warning("No data found for yesterday")
        sys.exit()

    logging.info(f"Query result: {row}")

    # --------------------------------------------------
    # 🔹 INSERT INTO DAILY SUMMARY TABLE
    # --------------------------------------------------

    insert_query = """
        INSERT INTO energy_19 (
            day_date,
            real_energy,

            avg_line_voltage_R,
            avg_line_voltage_Y,
            avg_line_voltage_B,

            avg_phase_voltage_R,
            avg_phase_voltage_Y,
            avg_phase_voltage_B,

            avg_line_current_R,
            avg_line_current_Y,
            avg_line_current_B,

            avg_power_factor,
            avg_frequency
        )
        VALUES (
            %s, %s,

            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,

            %s, %s
        )
        ON DUPLICATE KEY UPDATE
            real_energy = VALUES(real_energy),
            avg_line_voltage_R = VALUES(avg_line_voltage_R),
            avg_line_voltage_Y = VALUES(avg_line_voltage_Y),
            avg_line_voltage_B = VALUES(avg_line_voltage_B),
            avg_phase_voltage_R = VALUES(avg_phase_voltage_R),
            avg_phase_voltage_Y = VALUES(avg_phase_voltage_Y),
            avg_phase_voltage_B = VALUES(avg_phase_voltage_B),
            avg_line_current_R = VALUES(avg_line_current_R),
            avg_line_current_Y = VALUES(avg_line_current_Y),
            avg_line_current_B = VALUES(avg_line_current_B),
            avg_power_factor = VALUES(avg_power_factor),
            avg_frequency = VALUES(avg_frequency)
    """

    cursor.execute(insert_query, (yesterday_date, *row))
    conn.commit()

    logging.info("✅ Daily summary stored successfully")

    cursor.close()
    conn.close()

except Exception as e:
    logging.error(f"Script failed with error: {str(e)}")