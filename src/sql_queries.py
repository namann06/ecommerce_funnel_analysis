import sqlite3
import pandas as pd

def run_analytical_queries():
    db_path = "funnel_analysis.db"
    conn = sqlite3.connect(db_path)
    
    queries = {
        "1. Overall Funnel Conversion & Baseline Diagnostics": """
            SELECT 
                COUNT(Session_ID) AS Total_Sessions,
                SUM(Reached_Browse) AS Browse_Count,
                SUM(Reached_Add_to_Cart) AS Cart_Count,
                SUM(Reached_Checkout) AS Checkout_Count,
                SUM(Reached_Purchase) AS Purchase_Count,
                ROUND(100.0 * SUM(Reached_Browse) / COUNT(Session_ID), 2) AS Browse_Pct,
                ROUND(100.0 * SUM(Reached_Add_to_Cart) / COUNT(Session_ID), 2) AS Cart_Pct,
                ROUND(100.0 * SUM(Reached_Checkout) / COUNT(Session_ID), 2) AS Checkout_Pct,
                ROUND(100.0 * SUM(Reached_Purchase) / COUNT(Session_ID), 2) AS Purchase_Pct,
                ROUND(SUM(Total_Revenue), 2) AS Total_Revenue_USD
            FROM session_summary;
        """,
        
        "2. Step-by-Step Drop-Off & Micro-Conversion Rates": """
            WITH StageCounts AS (
                SELECT 
                    SUM(Reached_Browse) AS Browse,
                    SUM(Reached_Add_to_Cart) AS Cart,
                    SUM(Reached_Checkout) AS Checkout,
                    SUM(Reached_Purchase) AS Purchase
                FROM session_summary
            )
            SELECT 
                'Browse -> Add to Cart' AS Funnel_Step,
                Browse AS Step_Input,
                Cart AS Step_Output,
                Browse - Cart AS Dropped_Off,
                ROUND(100.0 * Cart / Browse, 2) AS Step_Conversion_Pct,
                ROUND(100.0 * (Browse - Cart) / Browse, 2) AS Step_Drop_Off_Pct
            FROM StageCounts
            UNION ALL
            SELECT 
                'Add to Cart -> Checkout' AS Funnel_Step,
                Cart AS Step_Input,
                Checkout AS Step_Output,
                Cart - Checkout AS Dropped_Off,
                ROUND(100.0 * Checkout / Cart, 2) AS Step_Conversion_Pct,
                ROUND(100.0 * (Cart - Checkout) / Cart, 2) AS Step_Drop_Off_Pct
            FROM StageCounts
            UNION ALL
            SELECT 
                'Checkout -> Purchase' AS Funnel_Step,
                Checkout AS Step_Input,
                Purchase AS Step_Output,
                Checkout - Purchase AS Dropped_Off,
                ROUND(100.0 * Purchase / Checkout, 2) AS Step_Conversion_Pct,
                ROUND(100.0 * (Checkout - Purchase) / Checkout, 2) AS Step_Drop_Off_Pct
            FROM StageCounts;
        """,

        "3. Channel Revenue Performance & ABM Account Acquisition Value": """
            SELECT 
                Channel,
                COUNT(Session_ID) AS Total_Sessions,
                SUM(Reached_Purchase) AS Total_Conversions,
                ROUND(100.0 * SUM(Reached_Purchase) / COUNT(Session_ID), 2) AS Channel_Conversion_Rate_Pct,
                ROUND(SUM(Total_Revenue), 2) AS Revenue_Generated,
                ROUND(SUM(Total_Revenue) / SUM(Reached_Purchase), 2) AS Average_Order_Value,
                ROUND(SUM(Total_Revenue) / COUNT(Session_ID), 2) AS Revenue_Per_Session
            FROM session_summary
            GROUP BY Channel
            ORDER BY Revenue_Generated DESC;
        """,

        "4. Device Drop-off Diagnostics (Identifying UX Friction Points)": """
            SELECT 
                Device,
                COUNT(Session_ID) AS Total_Sessions,
                SUM(Reached_Browse) AS Browse_Count,
                SUM(Reached_Add_to_Cart) AS Cart_Count,
                SUM(Reached_Checkout) AS Checkout_Count,
                SUM(Reached_Purchase) AS Purchase_Count,
                ROUND(100.0 * (COUNT(Session_ID) - SUM(Reached_Purchase)) / COUNT(Session_ID), 4) AS Overall_Drop_Off_Rate,
                ROUND(100.0 * (SUM(Reached_Checkout) - SUM(Reached_Purchase)) / SUM(Reached_Checkout), 2) AS Checkout_Friction_Drop_Off_Pct
            FROM session_summary
            GROUP BY Device
            ORDER BY Overall_Drop_Off_Rate DESC;
        """,

        "5. Region & Product Category High-Value Segment Diagnostics": """
            SELECT 
                Region,
                Product_Category,
                COUNT(Session_ID) AS Total_Sessions,
                SUM(Reached_Purchase) AS Completed_Orders,
                ROUND(SUM(Total_Revenue), 2) AS Total_Revenue,
                ROUND(100.0 * SUM(Reached_Purchase) / COUNT(Session_ID), 2) AS Conversion_Rate_Pct
            FROM session_summary
            GROUP BY Region, Product_Category
            ORDER BY Total_Revenue DESC
            LIMIT 10;
        """,

        "6. Financial Opportunity & Revenue Leakage Quantification (5% Reduction in Checkout Abandonment)": """
            WITH LeakageMetrics AS (
                SELECT 
                    SUM(Reached_Checkout) - SUM(Reached_Purchase) AS Checkout_Abandoners,
                    AVG(CASE WHEN Total_Revenue > 0 THEN Total_Revenue END) AS Current_AOV
                FROM session_summary
            )
            SELECT 
                Checkout_Abandoners AS Abandoned_Checkouts,
                ROUND(Current_AOV, 2) AS Avg_Order_Value,
                ROUND(Checkout_Abandoners * Current_AOV, 2) AS Total_Potential_Revenue_Lost,
                ROUND((Checkout_Abandoners * 0.05) * Current_AOV, 2) AS Recoverable_Revenue_At_5pct_Improvement,
                ROUND((Checkout_Abandoners * 0.10) * Current_AOV, 2) AS Recoverable_Revenue_At_10pct_Improvement
            FROM LeakageMetrics;
        """
    }
    
    print("\n=========================================================================")
    print("      ENTERPRISE FUNNEL DIAGNOSTICS & ABM VALUE CREATION QUERIES")
    print("=========================================================================\n")
    
    for title, query in queries.items():
        print(f"\n--- {title} ---")
        df_result = pd.read_sql_query(query, conn)
        print(df_result.to_string(index=False))
        print("-" * 75)
        
    conn.close()

if __name__ == "__main__":
    run_analytical_queries()
