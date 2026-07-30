import os
import sqlite3
import pandas as pd
import numpy as np

def run_etl():
    print("=== Starting Funnel Data Processing & SQLite Ingestion ===")
    
    csv_path = "funnel_analysis_data.csv"
    db_path = "funnel_analysis.db"
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Source file {csv_path} not found.")
        
    # 1. Load Raw CSV
    df_raw = pd.read_csv(csv_path)
    print(f"Loaded raw dataset: {df_raw.shape[0]} rows, {df_raw.shape[1]} columns.")
    
    # 2. Data Cleaning & Type Conversion
    df_clean = df_raw.copy()
    df_clean['Timestamp'] = pd.to_datetime(df_clean['Timestamp'])
    df_clean['Revenue'] = df_clean['Revenue'].fillna(0.0)
    
    # Clean whitespace strings if any
    for col in ['User_ID', 'Session_ID', 'Event', 'Device', 'Region', 'Channel', 'Product_Category']:
        df_clean[col] = df_clean[col].astype(str).str.strip()
        
    # Map Funnel Stage Hierarchy
    stage_mapping = {
        'Browse': 1,
        'Add to Cart': 2,
        'Checkout': 3,
        'Purchase': 4
    }
    df_clean['Stage_Order'] = df_clean['Event'].map(stage_mapping)
    
    # 3. Session-Level State Aggregation
    # Compute maximum stage reached, total revenue, session start/end time, and total event count
    session_agg = df_clean.groupby('Session_ID').agg(
        User_ID=('User_ID', 'first'),
        Session_Start=('Timestamp', 'min'),
        Session_End=('Timestamp', 'max'),
        Max_Stage_Order=('Stage_Order', 'max'),
        Total_Events=('Event', 'count'),
        Total_Revenue=('Revenue', 'sum'),
        Device=('Device', 'first'),
        Region=('Region', 'first'),
        Channel=('Channel', 'first'),
        Product_Category=('Product_Category', 'first')
    ).reset_index()
    
    # Calculate session duration in seconds
    session_agg['Duration_Seconds'] = (session_agg['Session_End'] - session_agg['Session_Start']).dt.total_seconds()
    
    # Map Max Stage Name
    max_stage_name_map = {1: 'Browse', 2: 'Add to Cart', 3: 'Checkout', 4: 'Purchase'}
    session_agg['Max_Stage_Reached'] = session_agg['Max_Stage_Order'].map(max_stage_name_map)
    
    # Stage Completion Flags (1 if reached, 0 otherwise)
    session_agg['Reached_Browse'] = (session_agg['Max_Stage_Order'] >= 1).astype(int)
    session_agg['Reached_Add_to_Cart'] = (session_agg['Max_Stage_Order'] >= 2).astype(int)
    session_agg['Reached_Checkout'] = (session_agg['Max_Stage_Order'] >= 3).astype(int)
    session_agg['Reached_Purchase'] = (session_agg['Max_Stage_Order'] >= 4).astype(int)
    
    # Analytical Flags
    # True Bounce = Session ended at Browse (only 1 event)
    session_agg['Is_True_Bounce'] = (session_agg['Total_Events'] == 1).astype(int)
    session_agg['Is_Converted'] = (session_agg['Reached_Purchase'] == 1).astype(int)
    
    # Drop-off stage identification
    def identify_drop_off(max_stage):
        if max_stage == 1:
            return 'Browse Drop-off'
        elif max_stage == 2:
            return 'Cart Abandonment'
        elif max_stage == 3:
            return 'Checkout Abandonment'
        else:
            return 'Converted (No Drop-off)'
            
    session_agg['Drop_Off_Stage'] = session_agg['Max_Stage_Order'].apply(identify_drop_off)
    
    # 4. Ingest into SQLite Database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Store raw events
    df_raw.to_sql('raw_events', conn, if_exists='replace', index=False)
    
    # Store cleaned events
    df_clean.to_sql('cleaned_events', conn, if_exists='replace', index=False)
    
    # Store session summary table
    session_agg.to_sql('session_summary', conn, if_exists='replace', index=False)
    
    # Create Funnel Metrics View
    cursor.execute("DROP VIEW IF EXISTS view_funnel_conversion_summary;")
    cursor.execute("""
        CREATE VIEW view_funnel_conversion_summary AS
        SELECT 
            COUNT(Session_ID) AS Total_Sessions,
            SUM(Reached_Browse) AS Total_Browse,
            SUM(Reached_Add_to_Cart) AS Total_Add_to_Cart,
            SUM(Reached_Checkout) AS Total_Checkout,
            SUM(Reached_Purchase) AS Total_Purchase,
            ROUND(100.0 * SUM(Reached_Browse) / COUNT(Session_ID), 2) AS Pct_Browse,
            ROUND(100.0 * SUM(Reached_Add_to_Cart) / COUNT(Session_ID), 2) AS Pct_Add_to_Cart,
            ROUND(100.0 * SUM(Reached_Checkout) / COUNT(Session_ID), 2) AS Pct_Checkout,
            ROUND(100.0 * SUM(Reached_Purchase) / COUNT(Session_ID), 2) AS Pct_Purchase,
            SUM(Total_Revenue) AS Total_Revenue
        FROM session_summary;
    """)
    
    # Create Channel & Device Performance View
    cursor.execute("DROP VIEW IF EXISTS view_channel_device_performance;")
    cursor.execute("""
        CREATE VIEW view_channel_device_performance AS
        SELECT 
            Channel,
            Device,
            COUNT(Session_ID) AS Total_Sessions,
            SUM(Reached_Add_to_Cart) AS Total_Cart,
            SUM(Reached_Checkout) AS Total_Checkout,
            SUM(Reached_Purchase) AS Total_Purchases,
            ROUND(1.0 - (1.0 * SUM(Reached_Purchase) / COUNT(Session_ID)), 4) AS Drop_Off_Rate,
            ROUND(100.0 * SUM(Reached_Purchase) / COUNT(Session_ID), 2) AS Conversion_Rate_Pct,
            ROUND(SUM(Total_Revenue), 2) AS Channel_Device_Revenue,
            ROUND(AVG(CASE WHEN Total_Revenue > 0 THEN Total_Revenue END), 2) AS Avg_Order_Value
        FROM session_summary
        GROUP BY Channel, Device;
    """)
    
    conn.commit()
    conn.close()
    
    print("=== ETL Pipeline Successfully Completed! ===")
    print(f"Database created at: {os.path.abspath(db_path)}")
    print(f"Total Sessions Processed: {len(session_agg)}")
    print(f"Total Converted Sessions: {session_agg['Is_Converted'].sum()}")
    print(f"Overall Funnel Conversion Rate: {session_agg['Is_Converted'].mean()*100:.2f}%")

if __name__ == "__main__":
    run_etl()
