import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from pycaret.classification import *

st.set_page_config(
    page_icon="baseball",
    layout="wide",
)
st.title("Retention Model")


@st.cache()
def get_data_sets():

    df = pd.read_parquet("yankees-data-export-event.parquet")

    df = df.sample(frac=0.001)

    df_train = df.sample(frac=0.85, random_state=786)
    df_eval = df.drop(df_train.index)

    df_train.reset_index(drop=True)
    df_eval.reset_index(drop=True)

    return df, df_train, df_eval


def get_model(df_train, model_type):

    setup(
        data=df_train,
        target="did_purchase",
        train_size=0.80,
        data_split_shuffle=True,
        categorical_features=["inMarket"],
        date_features=["eventDate"],
        ignore_features=[
            "dimCustomerMasterId",
            "eventName",
            "minDaysOut",
            "maxDaysOut",
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
            "recent_openRate",
        ],
    )

    model_matrix = compare_models(fold=2, include=[model_type])

    best_model = create_model(model_matrix, fold=2)

    return best_model


def get_predictions(model, df_eval):

    df_inference = predict_model(model, data=df_eval, raw_score=True)

    return df_inference


def get_metrics(df_inference):

    accuracy = pycaret.utils.check_metric(
        df_inference["did_purchase"], df_inference["Label"], metric="Accuracy"
    )
    precision = pycaret.utils.check_metric(
        df_inference["did_purchase"], df_inference["Label"], metric="Precision"
    )
    recall = pycaret.utils.check_metric(
        df_inference["did_purchase"], df_inference["Label"], metric="Recall"
    )
    f1 = pycaret.utils.check_metric(
        df_inference["did_purchase"], df_inference["Label"], metric="F1"
    )
    auc = pycaret.utils.check_metric(
        df_inference["did_purchase"], df_inference["Label"], metric="AUC"
    )

    metrics = {
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "AUC": auc,
    }

    return metrics


def get_feature_importances(model):

    feature_columns = get_config("X_train").columns
    feature_values = model.feature_importances_

    df_feature_importances = pd.DataFrame(columns=["Feature", "Importance"])

    df_feature_importances["Feature"] = feature_columns
    df_feature_importances["Importance"] = feature_values

    df_feature_importances["Importance"] = pd.to_numeric(
        df_feature_importances["Importance"]
    )

    df_feature_importances = df_feature_importances.sort_values(by=["Importance"])

    df_feature_importances = df_feature_importances.iloc[0:12]

    return df_feature_importances


# SIDEBAR COMPONENTS
st.sidebar.markdown("### Select Options:")

dataset_type = st.sidebar.radio('Dataset:',
    ('dataset 1', 'dataset 2', 'dataset 3'))

model_type = st.sidebar.selectbox('Algorithm:',
     ('lightgbm', 'lr', 'rf'))

#st.sidebar.markdown("### Filter the Dataset:")

section_1 = st.expander("Hypothesis", expanded=True)
section_2 = st.expander("Raw Dataset", expanded=False)
section_3 = st.expander("Model Metrics", expanded=True)
section_4 = st.expander("Score Distribution", expanded=True)

# SECTION 0 : HYPOTHESIS
with section_1:

    st.markdown(
        """
        Tell the user a bit about how to use this Streamlit app.	
    """
    )

# SECTION 2 : DATASET
with section_2:

    df, df_train, df_eval = get_data_sets()
    st.write(df)

    st.write("Data used for training:", df_train.shape)
    st.write("Data used for evaluation:", df_eval.shape)

# SECTION 3 : METRICS
with section_3:

    model = get_model(df_train, model_type)
    df_inference = get_predictions(model, df_eval)
    metrics = get_metrics(df_inference)

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


# SECTION 4: SCORE DISTRIBUTION
with section_4:

    col_1, col_2 = st.columns(2)

    with col_1:
        fig, ax = plt.subplots(figsize=(5, 2))
        ax.hist(df_inference["Score_0"], bins=30)
        ax.set_title("Did Not Purchase", size=9)
        ax.set_ylabel("Count", fontsize=7)
        ax.set_xlabel("Probability", fontsize=7)

        st.pyplot(fig)

    with col_2:
        fig2, ax = plt.subplots(figsize=(5, 2))
        ax.hist(df_inference["Score_1"], bins=30)
        ax.set_title("Did Purchase", size=9)
        ax.set_ylabel("Count", fontsize=7)
        ax.set_xlabel("Probability", fontsize=7)

        st.pyplot(fig2)

# STYLE HACKS
with open("app.css", "r") as css_file:
    css = css_file.read()

st.markdown(css, unsafe_allow_html=True)
