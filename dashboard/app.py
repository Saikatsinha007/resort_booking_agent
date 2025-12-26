import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Resort Operations", layout="wide")

st.title("🏨 Resort Operations Dashboard")

API_URL = "http://localhost:8000"

def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/{endpoint}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch {endpoint}")
            return []
    except Exception as e:
        st.error(f"Connection error: {e}")
        return []

# Auto-refresh logic
if st.button("Refresh Data"):
    st.rerun()

col1, col2 = st.columns(2)

with col1:
    st.header("🍽️ Restaurant Orders")
    orders = fetch_data("orders")
    if orders:
        df_orders = pd.DataFrame(orders)
        # Reorder columns for better visibility
        if not df_orders.empty:
            cols = ["id", "room_number", "status", "total_amount", "items", "created_at"]
            # Filter cols that exist
            cols = [c for c in cols if c in df_orders.columns]
            
            # Format items column
            if "items" in df_orders.columns:
                df_orders["items"] = df_orders["items"].apply(
                    lambda x: ", ".join([f"{int(i['quantity'])}x {i['name']}" for i in x]) if isinstance(x, list) else str(x)
                )

            st.dataframe(df_orders[cols], use_container_width=True)
    else:
        st.info("No orders found.")

with col2:
    st.header("🧹 Service Requests")
    requests_data = fetch_data("requests")
    if requests_data:
        df_requests = pd.DataFrame(requests_data)
        if not df_requests.empty:
            cols = ["id", "room_number", "status", "request_type", "details", "created_at"]
            cols = [c for c in cols if c in df_requests.columns]
            st.dataframe(df_requests[cols], use_container_width=True)
    else:
        st.info("No service requests found.")

st.markdown("---")
st.caption("Dashboard updates manually via Refresh button or you can enable auto-refresh in code.")
