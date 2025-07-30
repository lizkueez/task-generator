import streamlit as st
import pandas as pd

st.set_page_config(page_title="RSOC Task Generator", page_icon="🐝", layout="wide")

st.title(":honeybee: RSOC Task Generator")
st.write("Upload a CSV file and select a task type to generate assignment suggestions.")

uploaded_file = st.file_uploader(":page_facing_up: Upload your CSV file", type=["csv"])

task_type = st.selectbox(":card_index_dividers: Select Task Type", ["", "Internal", "Partners"], index=0)

if task_type == "":
    st.info(":point_up: Please select a task type to continue.")

elif task_type in ["Internal", "Partners"]:
    try:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)

            df['Search ROI'] = df['Search ROI'].replace('[\$,]', '', regex=True).astype(float)
            df['Search ROI%'] = df['Search ROI%'].replace('[\%,]', '', regex=True).astype(float)
            df['Combined Score'] = df['Search ROI'] + df['Search ROI%']

            st.sidebar.markdown("### :gear: Filters")
            top_n = st.sidebar.number_input("1. How many top Original Post IDs?", min_value=1, value=5, step=1)

            with st.sidebar.expander("2. Include Post Tiers"):
                tier_options = ["Low", "Medium", "High"]
                selected_post_tiers = st.multiselect("Select Post Tiers", tier_options, default=tier_options)

            with st.sidebar.expander("3. Include Ad Creative Tiers"):
                selected_creative_tiers = st.multiselect("Select Creative Tiers", tier_options, default=tier_options)

            with st.sidebar.expander("4. Filter by Locale"):
                locales = df['Locale'].dropna().unique().tolist()
                selected_locales = st.multiselect("Select Locales", locales, default=locales)

            with st.sidebar.expander("5. Filter by Author"):
                authors = df['Ad Creative Author Name'].dropna().unique().tolist()
                selected_authors = st.multiselect("Select Authors", authors, default=authors)

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
            filtered_post_scores = post_scores[post_scores['Tier'].isin(selected_post_tiers)]
            filtered_post_scores = filtered_post_scores.sort_values(by='Search ROI', ascending=False)

            top_posts = filtered_post_scores.head(top_n)['Original Post ID'].tolist()

            tasks = []
            total_payment = 0

            for post_id in top_posts:
                post_data = filtered_df[filtered_df['Original Post ID'] == post_id]
                high_roi_creatives = post_data[post_data['Search ROI'] >= 5].copy()

                high_roi_creatives['Tier'] = high_roi_creatives['Search ROI'].apply(get_post_tier)
                high_roi_creatives = high_roi_creatives[high_roi_creatives['Tier'].isin(selected_creative_tiers)]

                if not high_roi_creatives.empty:
                    creative_ids = high_roi_creatives['Ad Creative Id'].unique().tolist()
                    media_types = high_roi_creatives[['Ad Creative Id', 'Ad Creative Media Type', 'Search ROI']].drop_duplicates()

                    image_count = media_types[media_types['Ad Creative Media Type'].str.lower() == 'image'].shape[0]
                    video_count = media_types[media_types['Ad Creative Media Type'].str.lower() == 'video'].shape[0]

                    total_pay = (image_count * 2 * 1) + (video_count * 2 * 3)
                    total_payment += total_pay

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
                        cid = str(row_c['Ad Creative Id']).replace('=\"', '').replace('\"', '')
                        tier = get_tier_emoji(row_c['Search ROI'])
                        roi = row_c['Search ROI']
                        id_with_tiers.append(f"{cid} {tier} (${roi:.0f})")

                    id_list = "\n".join(id_with_tiers)
                    id_label = "ID" if len(id_with_tiers) == 1 else "IDs"
                    id_only = ", ".join([str(cid).split()[0] for cid in id_with_tiers])

                    if task_type == "Partners":
                        website = post_data['Website Name'].iloc[0]
                        task_description = f"Based on {website}'s article, please create {creative_string} based on Ad Creative {id_label} {id_only}."
                        full_description = f"{task_description}\nSince this is a partner article, please make some changes so it's not copied 1:1.\nPlease find the link to upload below."
                    else:
                        task_description = f"Please create {creative_string} based on Ad Creative {id_label} {id_only}."
                        full_description = f"{task_description}\nPlease focus on policy compliancy.\nPlease find the link to upload below."

                    post_roi_sum = filtered_post_scores[filtered_post_scores['Original Post ID'] == post_id]['Search ROI'].values[0]
                    article_name = post_data['Original Article Name'].iloc[0] if 'Original Article Name' in post_data.columns else ""
                    tasks.append({
                        "Original Post ID": f"{post_id} (${post_roi_sum:.0f})",
                        "Article Name": article_name,
                        "Ad Creative IDs": id_list,
                        "Task Description": task_description,
                        "Full Description": full_description,
                        "Total Pay ($)": f"${total_pay}"
                    })

            if tasks:
                st.success(f"✅ Generated {len(tasks)} task(s).")
                task_df = pd.DataFrame(tasks)

                headers = st.columns([1, 1.5, 2, 3, 1, 1])
                headers[0].markdown("**Original Post ID**")
                headers[1].markdown("**Article Name**")
                headers[2].markdown("**Ad Creative ID**")
                headers[3].markdown("**Task Description**")
                headers[4].markdown("**Total Pay**")
                headers[5].markdown("**Copy**")

                for i, row in task_df.iterrows():
                    cols = st.columns([1, 1.5, 2, 3, 1, 1])
                    cols[0].markdown(f"**{row['Original Post ID']}**")
                    cols[1].markdown(row['Article Name'])
                    cols[2].markdown(f"<pre style='font-size: 16px'>{row['Ad Creative IDs']}</pre>", unsafe_allow_html=True)
                    cols[3].markdown(row["Task Description"])
                    cols[4].markdown(row["Total Pay ($)"])
                    with cols[5]:
                        st.button("📋 Copy", key=f"copy_{i}", help=row['Full Description'])

                st.markdown(f"### 💰 Total Pay for All Tasks: **${total_payment}**")

            else:
                st.warning("No qualifying creatives found for the selected filters.")

    except Exception as e:
        st.error(f"⚠️ Error processing file: {e}")

else:
    st.warning("🚧 This task type hasn’t been built yet. Check back soon!")

# Tier Key moved to bottom of sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("### :bookmark_tabs: Tier Key")
    st.markdown("**Post & Creative Tier Legend:**")
    st.markdown("🟢 High ROI: $51+")
    st.markdown("🟡 Medium ROI: $21–50")
    st.markdown("🔴 Low ROI: $5–20")
