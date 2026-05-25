# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 13:01:33 2025

@author: Admin
"""

import streamlit as st
import mysql.connector
import pandas as pd
from bokeh.plotting import figure,show
from bokeh.models import HoverTool,ColumnDataSource,Span,FactorRange


# Set a more appealing page configuration
st.set_page_config(layout="wide", page_title="Power Monitoring Dashboard", page_icon="⚡")

# Custom CSS for a modern, sleek look
st.markdown(
    """
    <style>
    /* Main container and sidebar styling */
    .st-emotion-cache-18ni7ap { /* Main app container */
        background-color: #f0f2f6;
    }
    .st-emotion-cache-1cypcdb { /* Another part of the main container */
        background-color: #f0f2f6;
    }
    .st-emotion-cache-13ln4j2 { /* More main container styling */
        background-color: #f0f2f6;
    }
    
    [data-testid="stSidebar"] {
        background-color: #31336c; /* Dark blue from the image */
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"] .st-emotion-cache-1r6r0i0 { /* Sidebar header/title */
        color: #e6e6fa; /* Light white for text */
        font-size: 1.5rem;
    }
    
    [data-testid="stSidebar"] .st-emotion-cache-1r6r0i0 p { /* Paragraphs in sidebar */
        color: #e6e6fa;
        font-size: 1.2rem;
    }

    .st-emotion-cache-1f8r84e { /* Another internal Streamlit element */
        background-color: #f0f2f6;
    }
    
    .st-emotion-cache-16txt4y { /* Selectbox label in sidebar */
        padding-left: 20px;
        background-color: #31336c;
    }
    
    .st-emotion-cache-16txt4y p {
        font-size: 20px;
        color: white;
    }

    /* Selectbox styling in sidebar */
    .st-emotion-cache-1n1v2ua { /* The selectbox itself */
        background-color: #4b58a1; /* A slightly lighter blue for the selectbox */
        color: white;
        border-radius: 5px;
        border: none;
    }
    
    .st-emotion-cache-1n1v2ua:hover {
        background-color: #5d6cb9; /* Darker on hover */
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #31336c; /* Dark blue for titles */
    }
    
    h4 {
        margin-top: -10%; /* Adjust as needed */
        margin-bottom: 20px;
    }

    /* Live data cards */
    .data-card {
        text-align: center;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Subtle shadow */
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    
    .data-card:hover {
        transform: translateY(-5px); /* Lift effect on hover */
    }
    
    .data-card-header {
        color: white;
        font-weight: bold;
        padding: 5px;
        border-radius: 5px 5px 0 0; /* Rounded top corners */
    }
    
    .data-card-value {
        font-size: 1.8rem; /* Larger font for values */
        font-weight: bold;
        color: #31336c; /* Dark blue for values */
        padding: 10px 0;
        background-color: white;
        border-radius: 0 0 10px 10px; /* Rounded bottom corners */
    }

    /* Color-coded headers for live data (matching image) */
    .red-header { background-color: #ef5350; } /* Material Red */
    .yellow-header { background-color: #ffca28; } /* Material Amber */
    .blue-header { background-color: #42a5f5; } /* Material Blue */
    .green-header { background-color: #66bb6a; } /* Material Green */

    /* Other elements */
    .stDateInput input { /* Date input fields */
        border: 2px solid #31336c;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True
)


def load_df():
    try:
        conndb=mysql.connector.connect(
            host="10.30.104.235",
            user="root",
            password="",
        )
        cursor = conndb.cursor()
        cursor.execute("SHOW DATABASES")
        dbs=[db[0] for db in cursor.fetchall()]
        req_db=[db for db in dbs if db.isdigit() and ((int(db)%10000>=2025 and int(db)/10000>=1))]
        db_list=[]
        for db in req_db:
            conn=mysql.connector.connect(
            host="localhost", # Changed to 10.30.104.235 from localhost based on your previous code
            user="root",
            password="",
            database=db
            )
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'meitest5'")
            table=cursor.fetchone()
            if table:
                cursor.execute("SELECT * FROM meitest5")
                rows=cursor.fetchall()
                columns=[desc[0] for desc in cursor.description]
                temp_df = pd.DataFrame(rows,columns=columns)
                db_list.append(temp_df)
        
        if not db_list:
            st.warning("No data found in the specified databases.")
            return pd.DataFrame() # Return empty DataFrame if no data

        df=pd.concat(db_list)
        df["Datetime"]=df["Datetime"].apply(lambda x: x+":00" if len(x.split(":")) == 2 else x)
        df["Datetime"]=pd.to_datetime(df["Datetime"],dayfirst=True)
        df["Datetime"]=df["Datetime"].apply(lambda x:x.replace(second=0))
        df.sort_values(by=['Datetime'], inplace=True)
        
        # Convert columns to float, handling potential errors for robustness
        for col in ["RealPower", "ApparentPower", "ReactivePower", "RealEnergyWH", "ApparentEnergyVAH",
                    "ReactiveEnergyVARHP", "ReactiveEnergyVARHN", "LineVoltageVRY", "LineVoltageVYB",
                    "LineVoltageVBR", "PhaseVoltageVRN", "PhaseVoltageVYN", "PhaseVoltageVBN",
                    "LineCurrentIR", "LineCurrentIY", "LineCurrentIB", "Frequency",
                    "RealPowerR", "RealPowerY", "RealPowerB", # Add phase powers
                    "ReactivePowerR", "ReactivePowerY", "ReactivePowerB", # Add phase reactive powers
                    "ApparentPowerR", "ApparentPowerY", "ApparentPowerB"]: # Add phase apparent powers
            df[col] = pd.to_numeric(df[col], errors='coerce') # 'coerce' will turn invalid parsing into NaN

        df["hour"]=df["Datetime"].dt.strftime("%Y-%m-%d %H")
        df["hour"]=pd.to_datetime(df["hour"])
        df["date"]=df["Datetime"].dt.date
        df["date"]=pd.to_datetime(df["date"])
        df["month"]=df["Datetime"].dt.strftime("%b %Y")
        df["year"]=df["Datetime"].dt.strftime("%Y")
        
        df["PowerFactor"]=df["PowerFactor"].replace('-1.00','1.00').astype(str) # Convert to string after cleaning
        
        return df

    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return pd.DataFrame() # Return empty DataFrame on error

df=load_df()

def Power():
    st.subheader("Power Graph")
    power_type = st.selectbox("Choose Power Type", ["RealPower","ApparentPower","ReactivePower"])
    col1, col2 = st.columns(2)
    with col1:
        date1 = st.date_input('Starting Date')
    with col2:
        date2 = st.date_input('Ending Date')
    
    if df.empty:
        st.warning("No data available to display.")
        return
        
    if pd.to_datetime(date1) > pd.to_datetime(date2):
        st.error("The start date cannot be after the end date.")
    elif pd.to_datetime(date1) < df["date"].min() or pd.to_datetime(date2) > df["date"].max():
        st.error("The selected date range is out of the available data range.")
    else:
        start_minute=df[df["Datetime"].dt.date==pd.to_datetime(date1).date()].iloc[0]
        end_minute=df[df["Datetime"].dt.date==pd.to_datetime(date2).date()].iloc[-1]
        power_date=df[(df["Datetime"]>=start_minute["Datetime"]) & (df["Datetime"]<=end_minute["Datetime"])]
        
        if power_date.empty:
            st.warning("No data available for the selected date range.")
            return None
            
        source