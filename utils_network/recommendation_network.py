import streamlit as st

from utils_network.recommendation_modules.network_overview import network_overview
from utils_network.recommendation_modules.network_health import network_health
from utils_network.recommendation_modules.network_traffic import network_traffic
from utils_network.recommendation_modules.latency_packet_loss import latency_packet_loss
from utils_network.recommendation_modules.security_metrics import security_metrics
from utils_network.recommendation_modules.network_configuration import network_configuration
from utils_network.recommendation_modules.qos import qos
from utils_network.recommendation_modules.performance_by_location import performance_by_location
from utils_network.recommendation_modules.capacity_planning import capacity_planning
from utils_network.recommendation_modules.incident_downtime import incidents_downtime
from utils_network.recommendation_modules.monitoring_alerts import monitoring_alerts

def recommendation_network(df):
    st.header("📈 Network Performance Insights & Recommendations")

    network_overview(df)
    network_health(df)
    network_traffic(df)
    latency_packet_loss(df)
    security_metrics(df)
    network_configuration(df)
    qos(df)
    performance_by_location(df)
    capacity_planning(df)
    incidents_downtime(df)
    monitoring_alerts(df)
