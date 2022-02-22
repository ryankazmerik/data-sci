import altair as alt
from altair import datum
from PIL import Image

import datetime
import json
import pandas as pd
import numpy as np
import spacy
import spacy_streamlit
import streamlit as st
import uuid

st.set_page_config(page_icon='hammer_and_wrench', layout='wide',)
st.title("Dangerous Tool Analysis")


@st.cache(allow_output_mutation=True)
def load_model():

    ner = spacy.load('../models/tool_model')
    return ner


def load_data(model_version):

    df = pd.read_parquet('../models/tool_model/results_' +
                         model_version+'.parquet')

    tools_flat = []
    for idx, tools in enumerate(df['TOOLS']):

        for tool in tools:
            tools_flat.append({
                'ID': df['ID'].iloc[idx],
                'ACTIVITY': df['ACTIVITY'].iloc[idx],
                'DESCRIPTION': df['DESCRIPTION'].iloc[idx],
                'INCIDENT_DATE_TIME': df['INCIDENT_DATE_TIME'].iloc[idx],
                'OPERATING_AREA': df['OPERATING_AREA'].iloc[idx],
                'TOOL': tool,
                'INJURY_TREATMENT': df['INJURY_TREATMENT'].iloc[idx]
            })

    df_tools = pd.DataFrame(tools_flat, columns=[
        'ID', 'ACTIVITY', 'DESCRIPTION', 'INCIDENT_DATE_TIME', 'OPERATING_AREA', 'TOOL', 'INJURY_TREATMENT'])

    df_tools = df_tools.groupby(['TOOL', 'INJURY_TREATMENT']).agg({
        'ID': 'count',
        'ACTIVITY': 'first',
        'DESCRIPTION': 'first',
        'INCIDENT_DATE_TIME': 'first',
        'OPERATING_AREA': 'first'
    }).reset_index()

    return df_tools


# SIDEBAR COMPONENTS
st.sidebar.markdown('### Choose the Model:')

model_version = st.sidebar.selectbox(
    'MODEL VERSION:',
    ['v1'],
    format_func=lambda x: 'Tool Extractor ' + x)

chart_type = st.sidebar.radio(
    'CHART TYPE:',
    ['Frequency', 'Percentage'],
    index=1)

inc_hazards = st.sidebar.checkbox(
    label='Show Hazard IDs'
)

min_freq = st.sidebar.slider(
    'MINIMUM FREQUENCY:', 1, 20, value=8)

st.sidebar.markdown('### Filter the Dataset:')

activity = st.sidebar.multiselect(
    'ACTIVITY:',
    ['Completions', 'Construction - Facilities & Pipelines',
     'Construction - Lease & Road', 'Drilling',
     'Well, Pipeline & Facility Operations'])

op_area = st.sidebar.multiselect(
    'OPERATING AREA:',
    ['Anadarko Operations', 'Canadian Operations', 'Rockies Operations',
     'Southern Operations', 'Texas Operations'])

year = st.sidebar.slider(
    'YEAR:', min_value=2012, max_value=2021, value=(2012, 2021))  # hook up to INCIDENT_DATE_TIME


# MAIN SECTION COMPONENTS
left_col, right_col = st.beta_columns([3, 1])

with left_col:
    section_0 = st.beta_expander("Hypothesis")
    section_1 = st.beta_expander("Results", expanded=True)
    section_2 = st.beta_expander("Model")
    section_3 = st.beta_expander("Data")

    # SECTION 0 : HYPOTHESIS
    with section_0:

        st.markdown("## Heinrich / Bird Safety Pyramid")
        st.markdown("""
            Herbert W. Heinrich was a pioneering occupational health and safety researcher.
            His 1931 publication *Industrial Accident Prevention: A Scientific Approach*
            was based on the analysis of workplace injuries and accident data collected by 
            his employer, a large insurance company.
            
            The work was pursued and disseminated in the 1970’s by **Frank E. Bird**, who 
            worked for the insurance company of the North America. Bird analyzed more than 1.7 
            million accidents reported by 297 cooperating companies.	
        """)

        image = Image.open('./img/bird-theory.png')
        st.image(image, width=500)

        st.markdown("""
            Birds safety theory suggests that there is a 3:1 ratio between minor injuries (first-aid)
            and major injuries (medical-aid).
            
            **Using this ratio - we should be able to identify tools that are more dangerous (i.e 
            causing more major injuries than is typical.)**
        """)

    # SECTION 1 : VISUALIZATION
    with section_1:

        df_tools = load_data(model_version)
        plot_lines = [0.94, 0.98]

        if not inc_hazards:
            plot_lines = [0.75]
            df_tools = df_tools[df_tools['INJURY_TREATMENT'].str.contains("Aid", na=False)]
        
        if activity:
            df_tools = df_tools.loc[df_tools['ACTIVITY'].isin(activity)]

        if op_area:
            df_tools = df_tools.loc[df_tools['OPERATING_AREA'].isin(op_area)]

        if year:
            start = datetime.datetime.strptime(
                str(year[0])+'-01-01', "%Y-%m-%d")
            end = datetime.datetime.strptime(str(year[1])+'-12-31', "%Y-%m-%d")

            df_tools = df_tools.loc[
                (pd.to_datetime(df_tools['INCIDENT_DATE_TIME']) > start) &
                (pd.to_datetime(df_tools['INCIDENT_DATE_TIME']) < end)
            ]

        if chart_type == 'Frequency':

            by_freq = alt.Chart(df_tools).mark_bar().encode(
                x=alt.X('TOOL'),
                y=alt.Y('ID', title='COUNT'),
                color=alt.Color('INJURY_TREATMENT', scale=alt.Scale(
                    domain=['Medical Aid', 'First Aid', 'Accident w/o Injury'],
                    range=['#457FBF', '#F88D2B', '#8AE234']
                )),
                order=alt.Order(
                    'INJURY_TREATMENT',
                    sort='ascending'
                ),
                tooltip=[alt.Tooltip('TOOL', title='Tool'),
                         alt.Tooltip('ID', title='Count')]
            ).properties(
                title='Top Tools by Frequency',
                height=500,
                width=1000
            ).transform_joinaggregate(
                totals='sum(ID)',
                groupby=['TOOL']
            ).transform_filter(
                (datum.totals >= min_freq)
            ).configure_axisBottom(
                labelAngle=30
            )

            st.altair_chart(by_freq, use_container_width=True)

        elif chart_type == 'Percentage':
            by_percent = alt.Chart(df_tools).mark_bar().encode(
                x='TOOL',
                y=alt.Y('ID', stack="normalize", axis=alt.Axis(
                    format='%', title='PERCENT')),
                color=alt.Color('INJURY_TREATMENT', scale=alt.Scale(
                    domain=['Medical Aid', 'First Aid', 'Accident w/o Injury'],
                    range=['#457FBF', '#F88D2B', '#8AE234'])),
                order=alt.Order(
                    'INJURY_TREATMENT',
                    sort='ascending'
                ),
                tooltip=[alt.Tooltip('TOOL', title='Tool'),
                         alt.Tooltip('ID', title='Count')]
            ).properties(
                title='Top Tools by Percent',
                height=500,
                width=1000
            ).transform_joinaggregate(
                totals='sum(ID)',
                groupby=['TOOL']
            ).transform_filter(
                (datum.totals >= min_freq)
            )

            #line = alt.Chart(pd.DataFrame({'y': plot_lines})).mark_rule(
            #    color='red', strokeDash=[5, 5]).encode(y='y')

            by_percent = by_percent #+ line

            st.altair_chart(by_percent.configure_axisBottom(
                labelAngle=30), use_container_width=True)

    # SECTION 2 : NER MODEL
    with section_2:

        texts = list(df_tools['DESCRIPTION'])

        ner = load_model()
        spacy_streamlit.visualize_ner(
            ner(" ".join(texts).replace(u'\u25AF', '')),
            labels=['TOOL'],
            show_table=False,
            title='',
            colors={"TOOL": "linear-gradient(90deg, #009CFF, #8BFCE7)"},
            sidebar_title='Extract Entities:',
        )

    # SECTION 3: DATAFRAME
    with section_3:
        st.write(df_tools)


# OBSERVATIONS PANEL
with right_col:

    section_4 = st.beta_expander("Make an Observation", expanded=False)
    with section_4:

        details = st.text_area("Details:", height=120)
        initials = st.text_input("Initials:")
        save = st.button("Save")

        if save:
            item = {
                'id': uuid.uuid4().hex,
                'date': datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                'initials': initials,
                'details': details,
                'settings': {
                    'Model Version': model_version,
                    'Chart Type': chart_type,
                    'Minimum Frequency': min_freq,
                    'Activity': activity,
                    'Operating Area': op_area,
                    'Year': year
                }
            }

            with open('observations.json') as json_file:
                data = json.load(json_file)
                data.append(item)

                with open('observations.json', 'w') as outfile:
                    json.dump(data, outfile)

    with open('observations.json') as json_file:
        observations = json.load(json_file)

        if(len(observations) == 0):
            st.write("No observations yet")

        else:
            more_info = st.checkbox('Show settings')
            for obs in observations:
                st.markdown("* "+obs['details'] +
                            "&nbsp;&nbsp;&nbsp;-"+obs['initials'])

                if more_info:
                    st.write(obs['settings'])

# STYLE HACKS
with open('app.css', 'r') as css_file:
    css = (css_file.read())

st.markdown(css, unsafe_allow_html=True)