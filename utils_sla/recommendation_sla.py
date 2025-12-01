import streamlit as st

from utils_sla.recommendation_modules.sla_overview import sla_overview
from utils_sla.recommendation_modules.sla_metrics import sla_metrics
from utils_sla.recommendation_modules.sla_trends import sla_trend
from utils_sla.recommendation_modules.sla_exceptions import sla_exceptions
from utils_sla.recommendation_modules.root_cause import root_cause
from utils_sla.recommendation_modules.service_impact import service_impact
from utils_sla.recommendation_modules.customer_feedback import customer_feedback
from utils_sla.recommendation_modules.service_improvement import service_improvement

def recommendation_sla(df):
    st.header("📈 SLA Compliance Recommendations")
    
     # 🔧 Normalize all column names to lowercase (safe guard)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    sla_overview(df)
    sla_metrics(df)
    sla_trend(df)
    sla_exceptions(df)
    root_cause(df)
    service_impact(df)
    customer_feedback(df)
    service_improvement(df)
