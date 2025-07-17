import streamlit as st
import pandas as pd

st.set_page_config(page_title="RSOC Task Generator", page_icon="🐝")

st.title("🐝 RSOC Task Generator")
st.write("Upload a CSV file with ROI data to get task suggestions instantly.")

uploaded_file = st.file_uploader("📄 Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # Clean numeric fields
        df['Search ROI'] = df['Search ROI'].replace('[\$,]', '', regex=True).astype(float)
        df['Search ROI%'] = df['Search ROI%'].replace('[\%,]', '', regex=True).astype(float)
        df['Combined Score'] = df['Search ROI'] + df['Search ROI%']

        # Sidebar filters
        st.sidebar.header("⚙️ Filters")

        # Locale filter
        locales = df['Locale'].dropna().unique().tolist()
        selected_locales = st.sidebar.multiselect("Filter by Locale", locales, default=locales)

        # Author filter
        authors = df['Ad Creative Author Name'].dropna().unique().tolist()
        selected_authors = st.sidebar.multiselect("Filter by Author", authors, default=authors)

        # Top N selector
        top_n = st.sidebar.selectbox("How many top creatives?", [5, 10, 20], index=0)

        # Apply filters
        filtered_df = df[
            (df['Locale'].isin(selected_locales)) &
            (df['Ad Creative Author Name'].isin(selected_authors))
        ]

        # Rank by Ad Creative ID
        creative_scores = filtered_df.groupby('Ad Creative Id').agg({
            'Search ROI': 'sum',
            'Search ROI%': 'mean',
            'Combined Score': 'mean'
        }).sort_values(by='Combined Score', ascending=False).reset_index()

        top_creatives = creative_scores.head(top_n)['Ad Creative Id'].tolist()

        # Generate task descriptions
        task_descriptions = [
            f"Please create 3 inspired versions based on Ad Creative ID {creative_id}. Please focus on policy compliancy."
            for creative_id in top_creatives
        ]

        result_df = pd.DataFrame({
            "Ad Creative ID": top_creatives,
            "Task Description": task_descriptions
        })

        st.success(f"✅ Showing top {top_n} creatives")
        st.dataframe(result_df)

    except Exception as e:
        st.error(f"⚠️ Error processing file: {e}")
