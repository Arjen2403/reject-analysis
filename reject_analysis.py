import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="IR-D Reject Analyzer", layout="wide")

def load_data(file):
    df = pd.read_csv(file)
    df['DateTimeID'] = pd.to_datetime(df['DateTimeID'])
    # Logic categorization for Chart 1
    df['LogicType'] = df['RejectCause'].apply(
        lambda x: 'Machine Trigger' if 'IS-Machine' in str(x) else 'Vision Logic'
    )
    return df

st.title("📊 IR-D Production Reject Analyzer")
st.markdown("Analyze IS-Machine performance and vision-based defect patterns.")

# File Uploader
uploaded_file = st.file_uploader("Upload your Rejects CSV file", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    # Sidebar Navigation
    st.sidebar.header("Filter Settings")
    machine_list = sorted(df['Line'].unique())
    selected_line = st.sidebar.selectbox("Select Machine (Line)", machine_list)
    
    # --- CHART 1: GLOBAL (Multi-Machine) ---
    st.header("1. Global Plant Overview")
    st.info("Why this chart? It compares all machines to see if rejects are caused by mechanical timing (Blue) or glass quality (Red).")
    global_data = df.groupby(['Line', 'LogicType'])['Rejected'].sum().reset_index()
    fig1 = px.bar(global_data, x='Line', y='Rejected', color='LogicType', 
                  barmode='stack', template="plotly_white", color_discrete_map={'Machine Trigger': '#1f77b4', 'Vision Logic': '#d62728'})
    st.plotly_chart(fig1, use_container_width=True)

    # Filter for the selected machine
    m_df = df[df['Line'] == selected_line]

    col1, col2 = st.columns(2)

    with col1:
        # --- CHART 2: PARETO ---
        st.header(f"2. Top Causes: Machine {selected_line}")
        st.write("Identifies the 'Vital Few' issues causing the most waste.")
        pareto = m_df.groupby('RejectCause')['Rejected'].sum().sort_values(ascending=False).head(10).reset_index()
        fig2 = px.bar(pareto, x='RejectCause', y='Rejected', color='Rejected', color_continuous_scale='Reds')
        st.plotly_chart(fig2, use_container_width=True)

        # --- CHART 4: CAVITY RANKING ---
        st.header(f"4. Cavity 'Bad Actors'")
        st.write("Helps differentiate between a machine-wide issue and a specific mold failure.")
        cavity = m_df.groupby('Cavity')['Rejected'].sum().sort_values(ascending=False).head(12).reset_index()
        fig4 = px.bar(cavity, x='Cavity', y='Rejected', color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        # --- CHART 3: TIMELINE ---
        st.header(f"3. 24-Hour Trend")
        st.write("A steady line means stability; spikes indicate events like swabs or jams.")
        timeline = m_df.groupby('DateTimeID')['Rejected'].sum().reset_index()
        fig3 = px.line(timeline, x='DateTimeID', y='Rejected')
        st.plotly_chart(fig3, use_container_width=True)

        # --- CHART 5: HEATMAP ---
        st.header(f"5. Section/Gob Heatmap")
        st.write("Visualizes mechanical patterns in the IS-Machine layout.")
        heatmap_data = m_df.pivot_table(index='SectionPosition', columns='GobPosition', 
                                              values='Rejected', aggfunc='sum').fillna(0)
        fig5 = go.Figure(data=go.Heatmap(z=heatmap_data.values, x=heatmap_data.columns, 
                                         y=heatmap_data.index, colorscale='YlOrRd'))
        fig5.update_layout(xaxis_title="Gob Position", yaxis_title="Section Number")
        st.plotly_chart(fig5, use_container_width=True)

else:
    st.warning("Please upload a CSV file to begin analysis.")