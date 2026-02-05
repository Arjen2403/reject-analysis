import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="IR-D Reject Analyzer", layout="wide")

def load_data(file):
    df = pd.read_csv(file)
    df['DateTimeID'] = pd.to_datetime(df['DateTimeID'])
    # Categorize Logic Type: IS-Machine vs Vision System
    df['LogicType'] = df['RejectCause'].apply(
        lambda x: 'Machine Trigger' if 'IS-Machine' in str(x) else 'Vision Logic'
    )
    return df

st.title("📊 IR-D Production Reject Analyzer")
st.markdown("Dynamic analysis of IS-Machine and Vision-based rejection patterns.")

# File Uploader
uploaded_file = st.file_uploader("Upload your Rejects CSV file", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    # Identify active machines in the data
    active_machines = sorted(df['Line'].unique())
    
    # --- CHART 1: GLOBAL (Only Active Machines) ---
    st.header("1. Global Plant Overview")
    st.info("Overview of machines currently active in the dataset. Compares Mechanical vs. Vision triggers.")
    global_data = df.groupby(['Line', 'LogicType'])['Rejected'].sum().reset_index()
    fig1 = px.bar(global_data, x='Line', y='Rejected', color='LogicType', 
                  barmode='stack', template="plotly_white",
                  color_discrete_map={'Machine Trigger': '#1f77b4', 'Vision Logic': '#d62728'})
    st.plotly_chart(fig1, use_container_width=True)

    # Sidebar for individual machine selection
    st.sidebar.header("Individual Machine Deep-Dive")
    selected_line = st.sidebar.selectbox("Select Machine to Analyze", active_machines)
    
    # Filter data for the specific machine
    m_df = df[df['Line'] == selected_line]

    st.divider()
    st.header(f"🔍 Detailed Analysis: Machine {selected_line}")

    # Layout for charts 2-5
    col1, col2 = st.columns(2)

    with col1:
        # --- CHART 2: TOP CAUSES ---
        st.subheader("2. Top Reject Causes")
        st.write("Ranking the specific causes responsible for the most rejected bottles on this line.")
        pareto = m_df.groupby('RejectCause')['Rejected'].sum().sort_values(ascending=False).head(10).reset_index()
        fig2 = px.bar(pareto, x='RejectCause', y='Rejected', color='Rejected', color_continuous_scale='Reds')
        st.plotly_chart(fig2, use_container_width=True)

        # --- CHART 4: CAVITY BAD ACTORS ---
        st.subheader("4. Cavity 'Bad Actors'")
        st.write("Identifies underperforming molds that may require maintenance.")
        cavity = m_df.groupby('Cavity')['Rejected'].sum().sort_values(ascending=False).head(12).reset_index()
        fig4 = px.bar(cavity, x='Cavity', y='Rejected', color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        # --- CHART 3: 24-HOUR TREND ---
        st.subheader("3. 24-Hour Trend Graph")
        st.write("Monitors process stability over time. High peaks represent significant production events.")
        timeline = m_df.groupby('DateTimeID')['Rejected'].sum().reset_index()
        fig3 = px.line(timeline, x='DateTimeID', y='Rejected')
        fig3.update_traces(line_color='#2CA02C')
        st.plotly_chart(fig3, use_container_width=True)

        # --- CHART 5: SECTION/GOB HEATMAP ---
        st.subheader("5. Section/Gob Heatmap")
        st.write("Maps rejects to the physical IS-Machine layout to find mechanical patterns.")
        heatmap_data = m_df.pivot_table(index='SectionPosition', columns='GobPosition', 
                                        values='Rejected', aggfunc='sum').fillna(0)
        fig5 = go.Figure(data=go.Heatmap(z=heatmap_data.values, x=heatmap_data.columns, 
                                         y=heatmap_data.index, colorscale='YlOrRd'))
        fig5.update_layout(xaxis_title="Gob Position", yaxis_title="Section Number")
        st.plotly_chart(fig5, use_container_width=True)

else:
    st.warning("Please upload a CSV file to generate the analysis.")