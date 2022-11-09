import streamlit as st
from PIL import Image

def main(msg):



    favicon = Image.open('./images/ds-icon-white.ico')
    icon = Image.open('./images/ds-icon-white.png')

    st.set_page_config(
        page_title="StellarAlgo - Data Sci Dashboard",
        page_icon= favicon,
        layout="wide"
    )

    st.title(msg)


def get_message():

    return "Hello World"


if __name__ == "__main__":

    msg = get_message()

    main(msg)


    with open('./style.css') as css: st.markdown(css.read(), unsafe_allow_html=True)