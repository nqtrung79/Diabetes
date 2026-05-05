import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import recipe_service as rs
from datetime import datetime
import time

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Diabetes Research Factory", layout="wide")

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
    .nutrient-card { background-color: #f8f9fa; border-radius: 10px; padding: 15px; border: 1px solid #dee2e6; text-align: center; margin-bottom: 10px; min-height: 100px; }
    .nutrient-value { font-size: 18px; font-weight: bold; color: #2e7d32; }
    .nutrient-name { font-size: 13px; color: #616161; }
    .score-container { padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; border: 2px solid #ddd; color: white; }
    .ai-box { background-color: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 6px solid #007bff; color: #0d47a1; line-height: 1.6; }
    .stButton>button { border-radius: 20px; width: 100%; }
    /* Style cho Card bài viết */
    .article-card { border: 1px solid #eee; padding: 15px; border-radius: 10px; background: white; transition: 0.3s; }
    .article-card:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["USDA_Healthy_Food"]
# Collection mới cho bài viết
articles_col = db['food_articles']

st.markdown(
    "<div style='text-align:center; color:gray; margin-top:50px;'>© Data source: USDA's Food Composition'</div>",
    unsafe_allow_html=True)

# --- 4. ANTI-SPAM LOGIC ---
def is_spam(comment_text):
    bad_words = ['http', 'https', 'www', 'buy now', 'cờ bạc', 'quảng cáo']
    if any(word in comment_text.lower() for word in bad_words):
        return True
    if len(comment_text) < 3 or len(comment_text) > 1000:
        return True
    return False


# --- 5. DATA FETCHING ---
@st.cache_data
def get_raw_nutrients(fdc_id):
    pipeline = [
        {"$match": {"fdc_id": int(fdc_id)}},
        {"$lookup": {"from": "Nutrient_Definitions", "localField": "nutrient_id", "foreignField": "id",
                     "as": "details"}},
        {"$unwind": "$details"}
    ]
    results = list(db.Core_Nutrients.aggregate(pipeline))
    return pd.DataFrame(
        [{"Nutrient": r['details']['name'], "Amount": r['amount'], "Unit": r['details']['unit_name']} for r in results])


# --- 6. MAIN INTERFACE ---
st.title("🛡️ Decoding Food, Defeating Diabetes")

tab_explorer, tab_recommend, tab_about = st.tabs([
    "🍏 USDA Food Intelligence",
    "🛡️ Elite Foods Lab",
    "📄 About Project"
])

# --- TAB 1: EXPLORER (Giữ nguyên) ---
with tab_explorer:
    search_input = st.text_input("🔍 Search food name (e.g., Oats, Broccoli, Salmon)", key="usda_search")

    if 'page' not in st.session_state: st.session_state.page = 1
    skip = (st.session_state.page - 1) * 10

    query = {"description": {"$regex": search_input, "$options": "i"}} if search_input else {}
    scored_data = list(db.Scored_Foods.find(query).sort("score", -1).skip(skip).limit(10))
    df_display = pd.DataFrame(scored_data)

    if not df_display.empty:
        df_view = df_display[["icon", "description", "score", "status"]].copy()
        df_view.columns = ["Icon", "Food Description", "Score", "Rating"]
        event = st.dataframe(df_view, use_container_width=True, on_select="rerun", selection_mode="single-row",
                             hide_index=True)

        c1, _, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("⬅️ Previous Page"): st.session_state.page = max(1, st.session_state.page - 1)
        with c3:
            if st.button("Next Page ➡️"): st.session_state.page += 1

        if len(event.selection.rows) > 0:
            selected_food = scored_data[event.selection.rows[0]]
            fdc_id = selected_food['fdc_id']

            color_map = {1: "#1b5e20", 2: "#2e7d32", 3: "#f9a825", 4: "#ef6c00", 5: "#c62828", 6: "#8e0000"}
            bg_color = color_map.get(selected_food['rank'], "#757575")

            st.markdown(f"""
                <div class="score-container" style="background-color: {bg_color};">
                    <h1 style="font-size: 70px; margin:0;">{selected_food['icon']}</h1>
                    <h2 style="margin:0; color: white;">{selected_food['status']}</h2>
                    <h3 style="margin:0; color: white;">Diabetes Health Score: {selected_food['score']}/100</h3>
                </div>
            """, unsafe_allow_html=True)

            nut_df = get_raw_nutrients(fdc_id)
            st.subheader("📊 Full Nutrient Composition (USDA Standard per 100g)")
            cols = st.columns(5)
            for idx, row in nut_df.iterrows():
                with cols[idx % 5]:
                    st.markdown(f"""<div class="nutrient-card">
                        <div class="nutrient-name">{row['Nutrient']}</div>
                        <div class="nutrient-value">{round(row['Amount'], 2)} <small>{row['Unit']}</small></div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("💡 AI Virtual Expert Advice")
            advices = {
                1: "Excellent choice! This food has an ideal profile for blood sugar management.",
                2: "Safe for consumption. It fits well into a diabetic diet.",
                3: "Acceptable in moderation. Pair with high-fiber vegetables.",
                4: "Exercise caution. May cause moderate spikes.",
                5: "Not recommended. May negatively impact insulin sensitivity.",
                6: "Danger Zone! High risk of immediate glucose spikes."
            }
            expert_advice = advices.get(selected_food['rank'], "Data analysis in progress.")

            st.markdown(f"""<div class="ai-box">
                <b>🔬 Scientific Summary:</b> This item is classified as <b>{selected_food['status']}</b>.<br>
                <b>🌿 Dietary Guidance:</b> {expert_advice}
            </div>""", unsafe_allow_html=True)

            col_chart, col_recipe = st.columns([2, 1])
            with col_chart:
                fig = px.bar(nut_df.sort_values('Amount', ascending=False).head(15),
                             x='Amount', y='Nutrient', orientation='h',
                             title="Visual Nutrient Breakdown",
                             color='Amount', color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
            with col_recipe:
                rs.show_recipe_section(selected_food['description'])

# --- TAB 2: ELITE FOODS LAB ---
with tab_recommend:
    st.header("🔬 Elite Foods Lab: Research Insights")
    st.write("Deep-dive articles and community discussions on top-tier diabetic foods.")

    # A. Admin Editor (Expandable)
    with st.expander("🛠️ Content Management (Admin Only)"):
        with st.form("admin_post_form"):
            new_title = st.text_input("Food Name")
            new_cat = st.selectbox("Category", ["Beans", "Nuts", "Seeds", "Greens", "Supplements"])
            new_img = st.text_input("Image URL (Direct link)")
            new_content = st.text_area("Detailed Scientific Analysis/Article", height=200)
            if st.form_submit_button("Publish Article"):
                if new_title and new_content:
                    articles_col.insert_one({
                        "title": new_title, "category": new_cat, "image": new_img,
                        "content": new_content, "date": datetime.now(), "comments": []
                    })
                    st.success("Article Published!")
                    st.rerun()

    # B. Display Articles in Grid
    articles = list(articles_col.find().sort("date", -1))
    if not articles:
        st.info("No articles published yet.")
    else:
        grid_cols = st.columns(3)
        for idx, art in enumerate(articles):
            with grid_cols[idx % 3]:
                # SỬA TẠI ĐÂY: Thay 'selected_doc' bằng 'art' (biến trong vòng lặp)
                img_url = art.get('image', '').strip()

                if not img_url or not img_url.startswith("http"):
                    img_url = "https://via.placeholder.com/300x200?text=No+Image"

                st.markdown(f'<div class="article-card">', unsafe_allow_html=True)
                try:
                    st.image(img_url, use_container_width=True)
                except:
                    st.error("Image load error")

                st.subheader(art['title'])
                st.caption(f"📅 {art['date'].strftime('%Y-%m-%d')}")

                # Nút bấm để xem chi tiết bài viết
                if st.button(f"Read Details", key=f"btn_{art['_id']}"):
                    st.session_state.selected_article_id = art['_id']
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # C. Article Detail View (Khi người dùng nhấn chọn một bài)
    if 'selected_article_id' in st.session_state:
        st.markdown("---")
        # Tìm bài viết chi tiết dựa trên ID đã lưu trong session_state
        art_detail = articles_col.find_one({"_id": st.session_state.selected_article_id})

        if art_detail:
            det_col1, det_col2 = st.columns([1, 2])
            with det_col1:
                detail_img = art_detail.get('image', '').strip()
                if not detail_img.startswith("http"):
                    detail_img = "https://via.placeholder.com/300x200?text=No+Image"
                st.image(detail_img, use_container_width=True)

            with det_col2:
                st.title(art_detail['title'])
                st.info(f"Category: {art_detail['category']}")
                st.write(art_detail['content'])
                if st.button("✖️ Close Details"):
                    del st.session_state.selected_article_id
                    st.rerun()

            # --- PHẦN COMMENT (Giữ nguyên như code cũ của bạn) ---
            # ... (Phần code comment bên dưới)

            # Add Comment Form with Anti-Spam
            with st.form("comment_form", clear_on_submit=True):
                author = st.text_input("Your Name")
                msg = st.text_area("Add to discussion")
                if st.form_submit_button("Post Comment"):
                    # Rate limiting check
                    last_time = st.session_state.get('last_post_time', 0)
                    if time.time() - last_time < 60:
                        st.warning("Please wait 1 minute between comments to prevent spam.")
                    elif is_spam(msg):
                        st.error("Comment rejected: Potential spam or invalid format.")
                    elif msg:
                        new_cmt = {
                            "author": author if author else "Anonymous",
                            "text": msg,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        articles_col.update_one({"_id": art_detail['_id']}, {"$push": {"comments": new_cmt}})
                        st.session_state.last_post_time = time.time()
                        st.success("Comment posted!")
                        st.rerun()

# --- TAB 3: ABOUT (Giữ nguyên) ---
with tab_about:
    st.header("Research Project Overview")
    st.write(f"**Researcher:** Trung Nguyen")
    st.markdown("""
    **Project Objective:** 
    To provide a data-driven intelligence platform for analyzing food nutrients specifically for diabetic health management.

    **Methodology:**
    - Integration of USDA FoodData Central.
    - Multi-factor scoring algorithm.
    - 6-level health classification system.
    """)
    st.info("System optimized for Environmental Toxicology and Nutritional Research.")

st.markdown(
    "<div style='text-align:center; color:gray; margin-top:50px;'>© 2026 Research Intelligence | Lab Data Synthesis | All Rights Reserved</div>",
    unsafe_allow_html=True)