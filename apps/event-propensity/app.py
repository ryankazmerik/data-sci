import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from pycaret.classification import *

st.set_page_config(
    page_icon="baseball",
    layout="wide",
)

@st.cache()
def get_data_sets():

    df = pd.read_parquet("yankees-data.parquet")

    df = df.sample(frac=0.01)

    features = [
        "daysOut",
        "dimCustomerMasterId",
        "recent_openRate",
        "recent_clickRate",
        "eventDate",
        "eventName",
        "inMarket",
        "distanceToVenue",
        "tenure",
        "did_purchase",
        "events_purchased",
        "frequency_opponent",
        "frequency_eventDay",
        "frequency_eventTime"
    ]

    df = df[features]

    df_train = df.sample(frac=0.85, random_state=786)
    df_eval = df.drop(df_train.index)

    df_train.reset_index(drop=True)
    df_eval.reset_index(drop=True)

    return df, df_train, df_eval


def get_model(df_train, algos):

    setup(
        data= df_train, 
        target="did_purchase", 
        train_size = 0.85,
        data_split_shuffle=True,
        categorical_features=["daysOut"],
        ignore_features=["dimCustomerMasterId", "eventDate", "eventName"],
        silent=True,
        verbose=False,
        numeric_features=[
            "recent_openRate",
            "recent_clickRate",
            "distanceToVenue",
            "tenure",
            "events_purchased",
            "frequency_opponent",
            "frequency_eventDay",
            "frequency_eventTime"
        ]
    );

    model_matrix = compare_models(fold=2, include=[algos])

    best_model = create_model(model_matrix, fold=3)

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

    no_features = 10

    feature_columns = get_config("X_train").columns
    feature_values = model.feature_importances_

    df_feature_importances = pd.DataFrame(columns=["Feature", "Importance"])

    df_feature_importances["Feature"] = feature_columns[:no_features]
    df_feature_importances["Importance"] = feature_values[:no_features]

    df_feature_importances["Importance"] = pd.to_numeric(
        df_feature_importances["Importance"]
    )

    df_feature_importances = df_feature_importances.sort_values(by=["Importance"])

    df_feature_importances = df_feature_importances.iloc[0:12]

    return df_feature_importances

st.sidebar.header("StellarAlgo Machine Learning:")

model = st.sidebar.radio('Select Model:', ['Event Propensity','Product Propensity', 'Retention'])
# SIDEBAR COMPONENTS

choices = {
    'ada':'Ada Boosting Classifier',
    'dt':'Decision Tree Classifier',
    'et':'Extra Trees Classifier',
    'gbc':'Gradient Boosting Classifier',
    'lightgbm': 'Light Gradient Boosting Machine', 
    'rf': 'Random Forest',
    'xgboost': 'Extreme Gradient Boosting'
}
algos = st.sidebar.selectbox('Select Algorithm:', choices.keys(), format_func=lambda x:choices[x])

# MAIN SECTION COMPONENTS
section_1 = st.expander("Model Metrics", expanded=True)
section_2 = st.expander("Score Distribution & Feature Importances", expanded=True)
section_3 = st.expander("Association Heatmap", expanded=True)
section_4 = st.expander("Raw Dataset", expanded=False)

# SECTION 4 : DATASET
with section_4:

    df, df_train, df_eval = get_data_sets()
    st.write(df)
    
    st.write("Data used for training:", df_train.shape)
    st.write("Data used for evaluation:", df_eval.shape)

# SECTION 1 : METRICS
with section_1:

    model = get_model(df_train, algos)
    df_inference = get_predictions(model, df_eval)
    metrics = get_metrics(df_inference)

    col_1, col_2, col_3, col_4, col_5 = st.columns(5)
    
    with col_1:
        accuracy = st.metric(label="Accuracy", value=metrics["Accuracy"], delta="1.2 °F")

    with col_2:
        st.metric(label="Precision", value=metrics["Precision"], delta="1.2 °F")

    with col_3:
        st.metric(label="Recall", value=metrics["Recall"], delta="1.2 °F")

    with col_4:
        st.metric(label="F1", value=metrics["F1"], delta="1.2 °F")

    with col_5:
        st.metric(label="AUC", value=metrics["AUC"], delta="1.2 °F")

# SECTION 2: SCORE DISTRIBUTION & FEATURE IMPORTANCE
with section_2:

    col_1, col_2 = st.columns(2)

    with col_1:
        fig, ax = plt.subplots(figsize=(4, 2.5))
        ax.hist(df_inference["Score_1"], bins=30)
        ax.set_title("Did Purchase")
        ax.set_ylabel("Count", fontsize=7)
        ax.set_xlabel("Probability", fontsize=7)

        st.pyplot(fig)

    with col_2:
        df_features = get_feature_importances(model)

        fig3, ax = plt.subplots(figsize=(5, 4))
        ax.barh(df_features["Feature"], df_features["Importance"])
        ax.set_title("Importance by Feature", size=12)
        ax.set_ylabel("Feature", fontsize=12)
        ax.set_xlabel("Importance", fontsize=12)

        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontsize(9)

        st.pyplot(fig3)


# SECTION 3: ASSOCIATION HEATMAP
with section_3:

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.set(font_scale=0.6)

    heatmap = sns.heatmap(df_train.corr(), ax=ax, cmap="coolwarm")
    heatmap.set_xticklabels(
        heatmap.get_xticklabels(), rotation=45, horizontalalignment="right"
    )

    st.write(fig)


# STYLE HACKS
css = """
<style>
  h1 {
    font-size: 28px;
    padding: 0;
    margin-top: -50px;
    margin-bottom: 20px;
  }

  .streamlit-expanderHeader {
    font-weight: bold;
  }

  .stSelectbox label {
    font-weight: bold;
  }

  code {
    font-size: 14px;
  }

</style>
"""
st.markdown(css, unsafe_allow_html=True)
