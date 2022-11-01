import pandas as pd
import streamlit as st

pd.set_option('display.max_colwidth', None)
st.set_page_config(layout="wide")

session = None

# MAIN COMPONENTS
st.title("Model Training")
st.markdown("### To Be Implemented")

# SIDEBAR COMPONENTS
env_choices = {
    'Explore-US-DataScienceAdmin':'Explore-US',
    'QA-DataScienceAdmin':'QA',
    'US-StellarSupport':'US',
}

env = st.sidebar.selectbox('Environment:', env_choices.keys(), format_func=lambda x:env_choices[x])
model_type = st.sidebar.radio('Model:',('Event Propensity', 'Product Propensity', 'Retention'), index=1)
