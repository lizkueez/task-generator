import streamlit as st
import pandas as pd

st.set_page_config(page_title="RSOC Task Generator", page_icon="🐝")

st.title("🐝 RSOC Task Generator")
st.write("Upload a CSV file with ROI data to get task suggestions based on **Original Post ID**, media type, and freelancer pay.")

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

        # Group by Original Post ID, sum ROI
        post_scores = filtered_df.groupby('Original Post ID').agg({
            'Search ROI': 'sum',
            'Search ROI%': 'mean'
        }).sort_values(by='Search ROI', ascending=False).reset_index()

        top_posts = post_scores.head(top_n)['Original Post ID'].tolist()

        tasks = []

        for post_id in top_posts:
            post_data = filtered_df[filtered_df['Original Post ID'] == post_id]
            high_roi_creatives = post_data[post_data['Search ROI'] > 40]

            if not high_roi_creatives.empty:
                creative_ids = high_roi_creatives['Ad Creative Id'].unique().tolist()
                media_types = high_roi_creatives[['Ad Creative Id', 'Ad Creative Media Type']].drop_duplicates()

                # Count how many are images/videos
                image_count = media_types[media_types['Ad Creative Media Type'].str.lower() == 'image'].shape[0]
                video_count = media_types[media_types['Ad Creative Media Type'].str.lower() == 'video'].shape[0]

                total_pay = (image_count * 2 * 1) + (video_count * 2 * 3)

                # Generate media-specific wording
                parts = []
                if image_count > 0:
                    label = "image" if image_count * 2 == 1 else "images"
                    parts.append(f"{image_count * 2} inspired {label}")
                if video_count > 0:
                    label = "video" if video_count * 2 == 1 else "videos"
                    parts.append(f"{video_count * 2} inspired {label}")
                creative_string = " and ".join(parts)

                # Safe clean-up of Ad Creative IDs for Excel
                clean_creative_ids = [str(x).replace('="', '').replace('"', '') for x in creative_ids]
                id_list = ", ".join(clean_creative_ids)
                id_label = "ID" if len(clean_creative_ids) == 1 else "IDs"

                task_description = f"Please create {creative_string} based on Ad Creative {id_label} {id_list}. Please focus on policy compliancy."

                tasks.append({
                    "Original Post ID": str(post_id).replace('="', '').replace('"', ''),
                    "Ad Creative IDs": id_list,
                    "Task Description": task_description,
                    "Total Pay ($)": f"${total_pay}"
                })

        task_df = pd.DataFrame(tasks)

        if not task_df.empty:
            st.success(f"✅ Generated {len(task_df)} task(s) with pay breakdown.")
            st.write(task_df.style.set_properties(**{
                'white-space': 'pre-wrap',
                'word-wrap': 'break-word',
            }))
        else:
            st.warning("No qualifying creatives found over $40 ROI for the selected filters.")

    except Exception as e:
        st.error(f"⚠️ Error processing file: {e}")
