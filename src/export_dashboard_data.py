import sqlite3
import pandas as pd
import json
import os

def export_data():
    conn = sqlite3.connect("funnel_analysis.db")
    
    os.makedirs("app", exist_ok=True)
    
    # 1. Session summary list
    df_sessions = pd.read_sql_query("""
        SELECT 
            Session_ID, User_ID, Session_Start, Device, Region, Channel, Product_Category,
            Max_Stage_Reached, Total_Events, Total_Revenue, Is_True_Bounce, Is_Converted, Drop_Off_Stage,
            Reached_Browse, Reached_Add_to_Cart, Reached_Checkout, Reached_Purchase
        FROM session_summary
    """, conn)
    
    # Format Session_Start date string
    df_sessions['Date'] = pd.to_datetime(df_sessions['Session_Start']).dt.strftime('%Y-%m-%d')
    
    # Convert to records
    sessions_list = df_sessions.to_dict(orient='records')
    
    # 2. Daily Summary
    df_daily = pd.read_sql_query("""
        SELECT 
            DATE(Session_Start) AS Date,
            COUNT(Session_ID) AS Sessions,
            SUM(Reached_Purchase) AS Purchases,
            SUM(Total_Revenue) AS Revenue
        FROM session_summary
        GROUP BY DATE(Session_Start)
        ORDER BY Date ASC;
    """, conn)
    daily_list = df_daily.to_dict(orient='records')
    
    payload = {
        "sessions": sessions_list,
        "daily": daily_list
    }
    
    with open("app/dashboard_data.json", "w") as f:
        json.dump(payload, f)
        
    print(f"Exported {len(sessions_list)} sessions and {len(daily_list)} daily summary records to app/dashboard_data.json")
    conn.close()

if __name__ == "__main__":
    export_data()
