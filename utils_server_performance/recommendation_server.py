import streamlit as st

from utils_server_performance.recomendations_modules.server_overview import server_overview
from utils_server_performance.recomendations_modules.server_health import server_health
from utils_server_performance.recomendations_modules.server_utilization import server_utilization
from utils_server_performance.recomendations_modules.server_performance import server_performance
from utils_server_performance.recomendations_modules.server_availability import server_availability

def recommendation_server(df):
    st.header("📈 Server Performance Insights & Recommendations")

    server_overview(df)
    server_health(df)
    server_utilization(df)
    server_performance(df)
    server_availability(df)
