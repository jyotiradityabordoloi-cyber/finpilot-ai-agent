import streamlit as st

# Page configuration
st.set_page_config(
    page_title="FinPilot",
    page_icon="💼",
    layout="wide"
)

# Header
st.title("💼 FinPilot")
st.subheader("AI Month-End Close Agent")

st.write(
    "FinPilot helps finance teams investigate, reconcile, "
    "and understand month-end financial activity."
)

# Current project status
st.info("🚧 Prototype — Product discovery phase")

# Planned capabilities
st.markdown("## Planned Capabilities")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔍 Investigate")
    st.write("Find unusual transactions and financial exceptions.")

with col2:
    st.markdown("### 🔄 Reconcile")
    st.write("Match transactions with invoices and supporting documents.")

with col3:
    st.markdown("### 💡 Explain")
    st.write("Explain financial changes and recommend follow-up actions.")

# Product principle
st.markdown("## Product Principle")

st.success(
    "Automate repetitive work, assist with investigation, "
    "and keep consequential financial decisions under human control."
)

# Data notice
st.caption(
    "FinPilot will use synthetic financial data for this prototype. "
    "No real financial transactions will be processed."
)