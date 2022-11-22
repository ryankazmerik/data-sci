import pandas as pd
import streamlit as st
from PIL import Image

def main():

    favicon = Image.open('./images/ds-icon-white.ico')
    icon = Image.open('./images/sa-logo-twotone.png')

    st.set_page_config(
        page_title="StellarAlgo - Data Sci Dashboard",
        page_icon= favicon,
        layout="wide"
    )

    st.sidebar.image(icon)

    model_choices = {
        'Event Propensity':'Event Propensity',
        'Lead Recommender':'Product Propensity',
        'Data Analysis: Retention':'Retention',
    }

    header = st.container()
    
    with header:

        header_left, header_mid, header_right = st.columns(3)

        with header_left:
            reports = st.multiselect('Model Subtype:', model_choices.keys(), format_func=lambda x:model_choices[x], default=['Lead Recommender', 'Data Analysis: Retention'])
        
        with header_mid:
            quarters = st.multiselect('Quarter(s):',('Q1', 'Q2', 'Q3', 'Q4'), default='Q4')

        with header_right:
            year = st.multiselect('Year(s)', ('2022', '2021'), default='2022')

    
    df_usage = pd.read_csv("data/ml_usage_report.csv")

    df_filtered = df_usage[
        (df_usage["Year"].astype('str').isin(year)) & 
        (df_usage["Quarter"].isin(quarters)) & 
        (df_usage["Report"].isin(reports))
    ]
    
    total_hits = df_filtered["Count"].sum()
    total_teams = df_filtered["Tenant"].unique().size
    unique_users = df_filtered["User"].unique().size
    avg_hits_team = round(total_hits / total_teams, 2)
    avg_hits_week =  round(total_hits / 16, 2)

    col1, col2, col3 = st.columns(3)
    tab1, tab2, tab3, tab4 = st.tabs(['First Line', 'Second Line', 'Rookies', 'Veterans'])

    
    with col1:
        st.metric(label="Total Teams:", value=total_teams)
        st.metric(label="Unique Users:", value=unique_users)
    
    with col2:
        st.metric(label="Total Hits:", value=total_hits)
        st.metric(label="Avg Hits / Team:", value=avg_hits_team)
    
    with col3:
        st.metric(label="Avg Hits / Week:", value=avg_hits_week)
    
    with tab1:
        st.dataframe(df_filtered)
   

if __name__ == "__main__":

    
    main()


    with open('./style.css') as css: st.markdown(css.read(), unsafe_allow_html=True)