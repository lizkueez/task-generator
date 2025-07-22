import streamlit as st
import pandas as pd

st.set_page_config(page_title="RSOC Task Generator", page_icon="🐝", layout="wide")

st.title(":honeybee: RSOC Task Generator")
st.write("Upload a CSV file and select a task type to generate assignment suggestions.")

uploaded_file = st.file_uploader(":page_facing_up: Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    task_type = st.selectbox(":card_index_dividers: Select Task Type", ["", "SGs"], index=0)

    if task_type == "":
        st.info(":point_up: Please select a task type to continue.")

    elif task_type == "SGs":
        try:
            df = pd.read_csv(uploaded_file)

            df['Search ROI'] = df['Search ROI'].replace('[\$,]', '', regex=True).astype(float)
            df['Search ROI%'] = df['Search ROI%'].replace('[\%,]', '', regex=True).astype(float)
            df['Combined Score'] = df['Search ROI'] + df['Search ROI%']

            st.sidebar.header(":gear: Filters")
            locales = df['Locale'].dropna().unique().tolist()
            selected_locales = st.sidebar.multiselect("Filter by Locale", locales, default=locales)

            authors = df['Ad Creative Author Name'].dropna().unique().tolist()
            selected_authors = st.sidebar.multiselect("Filter by Author", authors, default=authors)

            top_n = st.sidebar.selectbox("How many top Original Post IDs?", [5, 10, 20], index=0)

            # NEW: Filter by ROI Tier for Original Post ID total ROI
            tier_options = ["Low", "Medium", "High"]
            selected_tiers = st.sidebar.multiselect("Include Post Tiers", tier_options, default=tier_options)

            def get_post_tier(total_roi):
                if total_roi >= 51:
                    return "High"
                elif total_roi >= 21:
                    return "Medium"
                elif total_roi >= 5:
                    return "Low"
                else:
                    return ""

            def get_tier_emoji(roi):
                if roi >= 51:
                    return "🟢"
                elif roi >= 21:
                    return "🟡"
                elif roi >= 5:
                    return "🔴"
                else:
                    return ""

            filtered_df = df[
                (df['Locale'].isin(selected_locales)) &
                (df['Ad Creative Author Name'].isin(selected_authors))
            ]

            post_scores = filtered_df.groupby('Original Post ID').agg({
                'Search ROI': 'sum',
                'Search ROI%': 'mean'
            }).reset_index()
            post_scores['Tier'] = post_scores['Search ROI'].apply(get_post_tier)
            filtered_post_scores = post_scores[post_scores['Tier'].isin(selected_tiers)]
            filtered_post_scores = filtered_post_scores.sort_values(by='Search ROI', ascending=False)

            st.subheader("Original Post ROI Totals")
            st.dataframe(filtered_post_scores[['Original Post ID', 'Search ROI', 'Tier']])

            top_posts = filtered_post_scores.head(top_n)['Original Post ID'].tolist()

            # NEW: Ad Creative ROI Summary
            st.subheader("Ad Creative ROI Totals")
            creative_summary = filtered_df.groupby('Ad Creative Id')['Search ROI'].sum().reset_index()
            creative_summary = creative_summary.sort_values(by='Search ROI', ascending=False)
            st.dataframe(creative_summary)

            tasks = []

            for post_id in top_posts:
                post_data = filtered_df[filtered_df['Original Post ID'] == post_id]
                high_roi_creatives = post_data[post_data['Search ROI'] >= 5]

                if not high_roi_creatives.empty:
                    creative_ids = high_roi_creatives['Ad Creative Id'].unique().tolist()
                    media_types = high_roi_creatives[['Ad Creative Id', 'Ad Creative Media Type', 'Search ROI']].drop_duplicates()

                    image_count = media_types[media_types['Ad Creative Media Type'].str.lower() == 'image'].shape[0]
                    video_count = media_types[media_types['Ad Creative Media Type'].str.lower() == 'video'].shape[0]

                    total_pay = (image_count * 2 * 1) + (video_count * 2 * 3)

                    parts = []
                    if image_count > 0:
                        label = "image" if image_count * 2 == 1 else "images"
                        parts.append(f"{image_count * 2} inspired {label}")
                    if video_count > 0:
                        label = "video" if video_count * 2 == 1 else "videos"
                        parts.append(f"{video_count * 2} inspired {label}")
                    creative_string = " and ".join(parts)

                    id_with_tiers = []
                    for _, row_c in media_types.iterrows():
                        cid = str(row_c['Ad Creative Id']).replace('="', '').replace('"', '')
                        tier = get_tier_emoji(row_c['Search ROI'])
                        id_with_tiers.append(f"{cid} {tier}")

                    id_list = ", ".join(id_with_tiers)
                    id_label = "ID" if len(id_with_tiers) == 1 else "IDs"

                    task_description = f"Please create {creative_string} based on Ad Creative {id_label} {id_list}. Please focus on policy compliancy."

                    tasks.append({
                        "Original Post ID": str(post_id).replace('="', '').replace('"', ''),
                        "Ad Creative IDs": id_list,
                        "Task Description": task_description,
                        "Total Pay ($)": f"${total_pay}"
                    })

            if tasks:
                st.success(f"✅ Generated {len(tasks)} task(s).")
                task_df = pd.DataFrame(tasks)

                for i, row in task_df.iterrows():
                    cols = st.columns([1, 2, 3, 1, 1])
                    cols[0].markdown(f"**{row['Original Post ID']}**")
                    cols[1].markdown(row["Ad Creative IDs"])
                    cols[2].markdown(row["Task Description"])
                    cols[3].markdown(row["Total Pay ($)"])
                    with cols[4]:
                        if st.button("📋 Copy", key=f"copy_{i}"):
                            st.info(f"📎 Task Description:\n\n{row['Task Description']}")

            else:
                st.warning("No qualifying creatives found for the selected filters.")

        except Exception as e:
            st.error(f"⚠️ Error processing file: {e}")

    else:
        st.warning("🚧 This task type hasn’t been built yet. Check back soon!")
