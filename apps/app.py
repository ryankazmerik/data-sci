import matplotlib.pyplot as plt
import pandas as pd
import pyodbc
import seaborn as sns
import streamlit as st

from pycaret.classification import *

st.set_page_config(page_icon='baseball', layout='wide',)
st.title("Event Propensity Model")

@st.cache()
def get_data_sets():

    df = pd.read_parquet('yankees-data-export-event.parquet')
    
    df = df.sample(frac=0.01)

    df_train = df.sample(frac=0.85, random_state=786)
    df_eval = df.drop(df_train.index)

    df_train.reset_index(drop=True)
    df_eval.reset_index(drop=True)

    return df, df_train, df_eval

def get_predictions(df_train, df_eval):

    setup(
        data= df_train, 
        target="did_purchase", 
        train_size = 0.80,
        data_split_shuffle=True,
        categorical_features=["inMarket"],
        date_features=["eventDate"],
        ignore_features=[
            "dimCustomerMasterId",
            "eventName",
            "minDaysOut",
            "maxDaysOut"
        ],
        silent=True,
        verbose=False,
        numeric_features=[
            "distanceToVenue",
            "events_purchased",
            "frequency_eventDay",
            "frequency_opponent",
            "frequency_eventTime",
            "recent_clickRate",
            "recent_openRate"
        ]
    )

    model_matrix = compare_models(
        fold= 2, 
        include= ["lr"]
    )
    
    best_model = create_model(
        model_matrix, 
        fold= 2
    )

    df_inference = predict_model(
        best_model, 
        data=df_eval, 
        raw_score=True
    )

    return df_inference

def get_metrics(df_inference):

    accuracy = pycaret.utils.check_metric(
        df_inference["did_purchase"], 
        df_inference["Label"], 
        metric="Accuracy"
    )
    precision = pycaret.utils.check_metric(
        df_inference["did_purchase"], 
        df_inference["Label"], 
        metric="Precision"
    )
    recall = pycaret.utils.check_metric(
        df_inference["did_purchase"], 
        df_inference["Label"], 
        metric="Recall"
    )
    f1 = pycaret.utils.check_metric(
        df_inference["did_purchase"], 
        df_inference["Label"], 
        metric="F1"
    )
    auc = pycaret.utils.check_metric(
        df_inference["did_purchase"], 
        df_inference["Label"], 
        metric="AUC"
    )

    metrics = {
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "AUC": auc
    }

    return metrics


# SIDEBAR COMPONENTS
st.sidebar.markdown('### Choose the Model:')

st.sidebar.markdown('### Filter the Dataset:')

section_0 = st.expander("Hypothesis")
section_1 = st.expander("Raw Dataset", expanded=False)
section_2 = st.expander("Model Metrics", expanded=False)
section_3 = st.expander("Association Heatmap", expanded=False)
section_4 = st.expander("Score Distribution", expanded=True)

# SECTION 0 : HYPOTHESIS
with section_0:

    st.markdown("""
        We think that by using previous buyer behaviour including ticketing, marketing and web data, 
        we can make a prediction on whether the fan will purchase a ticket for the next game or not.
        
        Authors: Matt Bahler, Pat Faith, Ryan Kazmerik, Joey Lai, Nakisa Rad, Shawn Sutherland	
    """)

# SECTION 1 : DATASET
with section_1:

    df, df_train, df_eval = get_data_sets()
    st.write(df)

    col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8 = st.columns(8)

    with col_1:
        st.write("Data used for training:",df_train.shape)
    
    with col_2:
        st.write("Data used for evaluation:",df_eval.shape)

# SECTION 2 : METRICS
with section_2:

    results = get_predictions(df_train, df_eval)
    metrics = get_metrics(results)

    col_1, col_2, col_3, col_4, col_5 = st.columns(5)
    
    with col_1:
        st.metric(label="Accuracy", value=metrics["Accuracy"], delta="1.2 °F")
    
    with col_2: 
        st.metric(label="Precision", value=metrics["Precision"], delta="1.2 °F")
    
    with col_3:
        st.metric(label="Recall", value=metrics["Recall"], delta="1.2 °F")
    
    with col_4:
        st.metric(label="F1", value=metrics["F1"], delta="1.2 °F")
    
    with col_5:
        st.metric(label="AUC", value=metrics["AUC"], delta="1.2 °F")
    
# SECTION 3: ASSOCIATION
with section_3:

    fig, ax = plt.subplots(figsize=(10,4))
    sns.set(font_scale = 0.6)
    
    heatmap = sns.heatmap(df_train.corr(), ax=ax, cmap="coolwarm")
    heatmap.set_xticklabels(heatmap.get_xticklabels(), rotation=45, horizontalalignment='right')

    st.write(fig)

# SECTION 4: SCORE DISTRIBUTION
with section_4:

    df_inference.hist(column=['Score_0', 'Score_1'], figsize=(30,5), layout=(1,3));

    st.write(df_inference)

# STYLE HACKS
with open('app.css', 'r') as css_file:
    css = (css_file.read())

st.markdown(css, unsafe_allow_html=True)

