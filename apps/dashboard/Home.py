import streamlit as st
from PIL import Image

favicon = Image.open('./images/ds-icon-white.ico')
icon = Image.open('./images/ds-icon-white.png')

st.set_page_config(
    page_title="StellarAlgo - Data Sci Dashboard",
    page_icon= favicon,
    layout="wide"
)

st.title("StellarAlgo - Data Science Dashboard")

with open('./style.css') as css: st.markdown(css.read(), unsafe_allow_html=True)