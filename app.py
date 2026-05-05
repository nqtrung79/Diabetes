import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import recipe_service as rs  # Giữ nguyên service của anh
from datetime import datetime
import time

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Diabetes Research Factory", layout="wide")

# --- 2. TỪ ĐIỂN ĐA NGÔN NGỮ ---
LANGUAGES = {
    "Tiếng Việt": {
        "title": "🛡️ Giải mã Thực phẩm, Đẩy lùi Tiểu đường",
        "tab1": "🍏 Trí tuệ Thực phẩm USDA",
        "tab2": "🛡️ Phòng thí nghiệm Elite",
        "tab3": "📄 Về dự án",
        "search_label": "🔍 Tìm tên thực phẩm (VD: Yến mạch, Bông cải)",
        "admin_title": "🛠️ Quản lý nội dung (Admin)",
        "food_name": "Tên thực phẩm",
        "category": "Nhóm",
        "publish_btn": "Xuất bản bài viết",
        "read_more": "Xem chi tiết",
        "discussion": "💬 Thảo luận",
        "comment_btn": "Gửi bình luận",
        "prev": "⬅️ Trang trước",
        "next": "Trang sau ➡️",
        "advice_title": "💡 Lời khuyên chuyên gia AI",
        "source": "© Nguồn dữ liệu: Thành phần thực phẩm của USDA"
    },
    "English": {
        "title": "🛡️ Decoding Food, Defeating Diabetes",
        "tab1": "🍏 USDA Food Intelligence",
        "tab2": "🛡️ Elite Foods Lab",
        "tab3": "📄 About Project",
        "search_label": "🔍 Search food name (e.g., Oats, Broccoli)",
        "admin_title": "🛠️ Content Management (Admin)",
        "food_name": "Food Name",
        "category": "Category",
        "publish_btn": "Publish Article",
        "read_more": "Read Details",
        "discussion": "💬 Discussion",
        "comment_btn": "Post Comment",
        "prev": "⬅️ Previous Page",
        "next": "Next Page ➡️",
        "advice_title": "💡 AI Virtual Expert Advice",
        "source": "© Data source: USDA's Food Composition"
    }
}

# --- 3. KẾT NỐI DATABASE ---
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["USDA_Healthy_Food"]
articles_col = db['food_articles']

# --- 4. SIDEBAR & CHỌN NGÔN NGỮ ---
if 'lang' not in st.session_state:
    st.session_state.lang = "Tiếng Việt"

with st.sidebar:
    st.title("🌐 Language / Ngôn ngữ")
    col_vn, col_us = st.columns(2)
    if col_vn.button("🇻🇳 Tiếng Việt", use_container_width=True):
        st.session_state.lang = "Tiếng Việt"
        st.rerun()
    if col_us.button("🇺🇸 English", use_container_width=True):
        st.session_state.lang = "English"
        st.rerun()

    st.divider()
    st.info(f"Đang dùng: {st.session_state.lang}")

L = LANGUAGES[st.session_state.lang]


# --- 5. LOGIC BỔ TRỢ (Spam, Nutrients) ---
def is_spam(text):
    bad_words = ['http', 'www', 'cờ bạc', 'quảng cáo', 'mua hàng']
    return any(w in text.lower() for w in bad_words) or len(text) < 3


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


# --- 6. GIAO DIỆN CHÍNH ---
st.title(L["title"])

tab_explorer, tab_recommend, tab_about = st.tabs([L["tab1"], L["tab2"], L["tab3"]])

# --- TAB 1: USDA EXPLORER ---
with tab_explorer:
    search_input = st.text_input(L["search_label"], key="usda_search")

    if 'page' not in st.session_state: st.session_state.page = 1
    skip = (st.session_state.page - 1) * 10

    query = {"description": {"$regex": search_input, "$options": "i"}} if search_input else {}
    scored_data = list(db.Scored_Foods.find(query).sort("score", -1).skip(skip).limit(10))

    if scored_data:
        df_view = pd.DataFrame(scored_data)[["icon", "description", "score", "status"]]
        event = st.dataframe(df_view, use_container_width=True, on_select="rerun", selection_mode="single-row",
                             hide_index=True)

        c_p, _, c_n = st.columns([1, 2, 1])
        if c_p.button(L["prev"]): st.session_state.page = max(1, st.session_state.page - 1)
        if c_n.button(L["next"]): st.session_state.page += 1

        if len(event.selection.rows) > 0:
            selected_food = scored_data[event.selection.rows[0]]
            # ... (Phần vẽ biểu đồ và hiển thị Rank/Score giữ nguyên như code cũ của anh)
            st.success(f"Selected: {selected_food['description']}")

# --- TAB 2: ELITE FOODS LAB (MongoDB Integrated) ---
with tab_recommend:
    # A. Admin Panel
    with st.expander(L["admin_title"]):
        with st.form("admin_post_form"):
            new_title = st.text_input(L["food_name"])
            new_cat = st.selectbox(L["category"], ["Beans", "Nuts", "Seeds", "Greens"])
            new_img = st.text_input("Image URL")
            new_content = st.text_area("Content")
            if st.form_submit_button(L["publish_btn"]):
                articles_col.insert_one({
                    "title": new_title, "category": new_cat, "image": new_img,
                    "content": new_content, "date": datetime.now(), "comments": []
                })
                st.rerun()

    # B. Bài viết & Comment
    articles = list(articles_col.find().sort("date", -1))
    cols = st.columns(3)
    for idx, art in enumerate(articles):
        with cols[idx % 3]:
            st.image(art.get('image') or "https://via.placeholder.com/300", use_container_width=True)
            st.subheader(art['title'])
            if st.button(L["read_more"], key=f"btn_{art['_id']}"):
                st.session_state.selected_art_id = art['_id']

    if 'selected_art_id' in st.session_state:
        st.divider()
        curr_art = articles_col.find_one({"_id": st.session_state.selected_art_id})
        if curr_art:
            st.header(curr_art['title'])
            st.write(curr_art['content'])

            # Thảo luận
            st.subheader(L["discussion"])
            for c in curr_art.get('comments', []):
                with st.chat_message("user"):
                    st.write(f"**{c['user']}**: {c['text']}")

            with st.form("cmt_form", clear_on_submit=True):
                u_n = st.text_input(L["name_label"])
                u_m = st.text_area(L["comment_label"])
                if st.form_submit_button(L["comment_btn"]):
                    if not is_spam(u_m):
                        new_cmt = {"user": u_n or "Anon", "text": u_m, "time": datetime.now().strftime("%H:%M")}
                        articles_col.update_one({"_id": curr_art["_id"]}, {"$push": {"comments": new_cmt}})
                        st.rerun()

            if st.button("✖"):
                del st.session_state.selected_art_id
                st.rerun()

# --- TAB 3: ABOUT ---
with tab_about:
    st.info("Environmental Toxicology and Nutritional Research - IET 2026")

st.markdown(f"<div style='text-align:center; color:gray;'>{L['source']}</div>", unsafe_allow_html=True)