import streamlit as st
import pandas as pd

st.set_page_config(page_title="RSOC Task Generator", page_icon="🐝")

st.title("🐝 RSOC Task Generator")
st.write("Upload a CSV file with ROI data to get task suggestions based on **Original Post ID**.")

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
        locales = df['Locale'].dropna().unique().tolist()
        selected_locales = st.sidebar.multiselect("Filter by Locale", locales, default=locales)

        authors = df['Ad Creative Author Name'].dropna().unique().tolist()
        selected_authors = st.sidebar.multiselect("Filter by Author", authors, default=authors)

        top_n = st.sidebar.selectbox("How many top Original Post IDs?", [5, 10, 20], index=0)

        # Apply filters
        filtered_df = df[
            (df['Locale'].isin(selected_locales)) &
            (df['Ad Creative Author Name'].isin(selected_authors))
        ]

        # Group by Original Post ID, sum ROI, then get creatives > $40
        post_scores = filtered_df.groupby('Original Post ID').agg({
            'Search ROI': 'sum',
            'Search ROI%': 'mean'
        }).sort_values(by='Search ROI', ascending=False).reset_index()

        top_posts = post_scores.head(top_n)['Original Post ID'].tolist()

        tasks = []
        for post_id in top_posts:
            post_data = filtered_df[filtered_df['Original Post ID'] == post_id]
            high_roi_creatives = post_data[post_data['Search ROI'] > 40]['Ad Creative Id'].unique().tolist()

            if high_roi_creatives:
                creative_count = len(high_roi_creatives)
                total_creatives = creative_count * 2
                id_label = "ID" if creative_count == 1 else "IDs"
                id_list = ", ".join(map(str, high_roi_creatives))

                task = {
                    "Original Post ID": post_id,
                    "Ad Creative IDs": id_list,
                    "Task Description": f"Please create {total_creatives} inspired creatives based on Ad Creative {id_label} {id_list}. Please focus on policy compliancy."
                }
                tasks.append(task)

        task_df = pd.DataFrame(tasks)

        if not task_df.empty:
            st.success(f"✅ Generated {len(task_df)} tasks based on top Original Post IDs.")
            st.dataframe(task_df)
        else:
            st.warning("No qualifying creatives found over $40 ROI for the selected filters.")

    except Exception as e:
        st.error(f"⚠️ Error processing file: {e}")
