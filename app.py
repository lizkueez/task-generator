import streamlit as st
import pandas as pd

st.set_page_config(page_title="RSOC Task Generator", page_icon="🐝")

st.title("🐝 RSOC Task Generator")
st.write("Upload a CSV file with ROI data to get task suggestions instantly.")

uploaded_file = st.file_uploader("📄 Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df['Search ROI'] = df['Search ROI'].replace('[\$,]', '', regex=True).astype(float)
        df['Search ROI%'] = df['Search ROI%'].replace('[\%,]', '', regex=True).astype(float)
        df['Combined Score'] = df['Search ROI'] + df['Search ROI%']

        creative_scores = df.groupby('Ad Creative Id').agg({
            'Search ROI': 'sum',
            'Search ROI%': 'mean',
            'Combined Score': 'mean'
        }).sort_values(by='Combined Score', ascending=False).reset_index()

        top_creatives = creative_scores.head(5)['Ad Creative Id'].tolist()
        task_descriptions = [
            f"Please create 3 inspired versions based on Ad Creative ID {creative_id}. Please focus on policy compliancy."
            for creative_id in top_creatives
        ]

        result_df = pd.DataFrame({
            "Ad Creative ID": top_creatives,
            "Task Description": task_descriptions
        })

        st.success("✅ Task list generated!")
        st.dataframe(result_df)

    except Exception as e:
        st.error(f"⚠️ Error processing file: {e}")
