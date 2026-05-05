import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import google.generativeai as genai
from datetime import datetime
import time
import requests

# --- 1. PAGE CONFIG (Bắt buộc ở đầu file) ---
st.set_page_config(page_title="Diabetes Research Factory", layout="wide")

# --- 2. CẤU HÌNH AI & AVATAR ---
# ANH THAY LINK ẢNH BÁC SỸ ĐẸP CỦA ANH VÀO ĐÂY
DOCTOR_AVATAR = "https://cdn-icons-png.flaticon.com/512/3304/3304567.png"

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. TỪ ĐIỂN ĐA NGÔN NGỮ ---
LANGUAGES = {
    "English": {
        "title": "🛡️ Decoding Food, Defeating Diabetes",
        "tab1": "🍏 USDA Food Intelligence",
        "tab2": "🛡️ Elite Foods Lab",
        "tab3": "📄 About Project",
        "food_type": "Food Type",
        "search_label": "🔍 Search food name (e.g., Oats, Broccoli)",
        "source": "© Data source: USDA's Food Composition",
        "advice_title": "💡 AI Virtual Expert Advice",
        "chat_label": "Bạn cần tư vấn về tiểu đường?",
        "chat_role": "You are a diabetes expert. Answer scientifically: ",
        "auth_title": "🔑 Account",
        "login": "Login",
        "register": "Register",
        "comment_section": "💬 Discussion",
        "post_btn": "Post Comment",
        "admin_title": "🛠️ Admin: Publish New Article"
    },
    "Tiếng Việt": {
        "title": "🛡️ Giải mã Thực phẩm, Đẩy lùi Tiểu đường",
        "tab1": "🍏 Trí tuệ Thực phẩm USDA",
        "tab2": "🛡️ Phòng thí nghiệm Elite",
        "tab3": "📄 Về dự án",
        "food_type": "Loại thực phẩm",
        "search_label": "🔍 Tìm tên thực phẩm (VD: Yến mạch, Bông cải)",
        "source": "© Nguồn dữ liệu: Thành phần thực phẩm của USDA",
        "advice_title": "💡 Lời khuyên từ Chuyên gia AI",
        "chat_label": "Bạn cần tư vấn về tiểu đường?",
        "chat_role": "Bạn là một chuyên gia về bệnh tiểu đường. Hãy trả lời khoa học: ",
        "auth_title": "🔑 Tài khoản",
        "login": "Đăng nhập",
        "register": "Đăng ký",
        "comment_section": "💬 Thảo luận",
        "post_btn": "Gửi bình luận",
        "admin_title": "🛠️ Admin: Đăng bài viết mới"
    }
}

# --- 4. CSS TÙY CHỈNH (HIỆN ĐẠI HÓA) ---
st.markdown(f"""
    <style>
    .nutrient-card {{ background-color: #f8f9fa; border-radius: 10px; padding: 15px; border: 1px solid #dee2e6; text-align: center; margin-bottom: 10px; }}
    .nutrient-value {{ font-size: 18px; font-weight: bold; color: #2e7d32; }}
    .score-container {{ padding: 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px; }}
    .ai-box {{ background-color: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 6px solid #007bff; color: #0d47a1; }}
    /* Avatar Chatbot Style */
    .doctor-trigger {{
        cursor: pointer; display: flex; align-items: center; gap: 10px;
        background: #e8f5e9; padding: 10px; border-radius: 50px; border: 1px solid #2e7d32;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIC DATABASE & WEBHOOK ---
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["USDA_Healthy_Food"]
articles_col = db['food_articles']


def send_to_webhook(data):
    try:
        requests.post(st.secrets["WEBHOOK_URL"], json=data, timeout=5)
    except:
        pass


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


# --- 6. SIDEBAR (NGÔN NGỮ & AUTH) ---
with st.sidebar:
    st.title("🛡️ Research Factory")

    # Chọn ngôn ngữ chuyên nghiệp bằng nút bấm
    col_v, col_e = st.columns(2)
    if col_v.button("🇻🇳 Tiếng Việt"): st.session_state.lang = "Tiếng Việt"
    if col_e.button("🇺🇸 English"): st.session_state.lang = "English"

    lang_key = st.session_state.get('lang', "Tiếng Việt")
    L = LANGUAGES[lang_key]

    st.divider()

    # Logic Auth với Webhook
    if 'user_email' not in st.session_state:
        st.subheader(L["auth_title"])
        auth_tab1, auth_tab2 = st.tabs([L["login"], L["register"]])
        with auth_tab1:
            e = st.text_input("Email", key="l_email")
            p = st.text_input("Mật khẩu", type="password", key="l_pw")
            if st.button(L["login"], use_container_width=True):
                send_to_webhook({"action": "LOGIN", "email": e})
                st.session_state.user_email = e
                st.rerun()
        with auth_tab2:
            if st.button("Tạo tài khoản mới", use_container_width=True):
                st.session_state.step = "DANG_KY_FORM"
                st.rerun()
    else:
        st.success(f"👤 {st.session_state.user_email}")
        if st.button("Đăng xuất"):
            del st.session_state.user_email
            st.rerun()

# --- 7. GIAO DIỆN CHÍNH ---
st.title(L["title"])

if st.session_state.get('step') == "DANG_KY_FORM":
    # --- FORM ĐĂNG KÝ CHI TIẾT ---
    st.header(L["register"])
    with st.form("reg_full"):
        fn = st.text_input("Họ và Tên*")
        em = st.text_input("Email*")
        un = st.text_input("Viện nghiên cứu/Trường*")
        pw = st.text_input("Mật khẩu*", type="password")
        if st.form_submit_button("✅ Hoàn tất"):
            send_to_webhook({"action": "REGISTER", "full_name": fn, "email": em, "uni": un})
            st.session_state.user_email = em
            st.session_state.step = "HOME"
            st.rerun()
    if st.button("⬅️ Quay lại"): st.session_state.step = "HOME"; st.rerun()

else:
    tab1, tab2, tab3 = st.tabs([L["tab1"], L["tab2"], L["tab3"]])

    # --- TAB 1: USDA EXPLORER (KHÔI PHỤC LOGIC CLICK & TÍNH TOÁN) ---
    with tab1:
        search_input = st.text_input(L["search_label"], key="usda_search")
        query = {"description": {"$regex": search_input, "$options": "i"}} if search_input else {}
        scored_data = list(db.Scored_Foods.find(query).sort("score", -1).limit(15))

        if scored_data:
            df_display = pd.DataFrame(scored_data)[["description"]]
            df_display.columns = [L["food_type"]]

            # Bảng dữ liệu cho phép Click hàng
            event = st.dataframe(df_display, use_container_width=True, on_select="rerun", selection_mode="single-row",
                                 hide_index=True)
            st.markdown(f"<p style='color:gray; font-size: 0.8rem;'>{L['source']}</p>", unsafe_allow_html=True)

            # Khi người dùng Click vào một hàng
            if len(event.selection.rows) > 0:
                selected_food = scored_data[event.selection.rows[0]]
                fdc_id = selected_food['fdc_id']

                # Hiển thị Score Card (Khôi phục logic màu sắc của anh)
                color_map = {1: "#1b5e20", 2: "#2e7d32", 3: "#f9a825", 4: "#ef6c00", 5: "#c62828", 6: "#8e0000"}
                bg_color = color_map.get(selected_food.get('rank', 3), "#757575")

                st.markdown(f"""
                    <div class="score-container" style="background-color: {bg_color};">
                        <h1 style="font-size: 60px; margin:0;">{selected_food.get('icon', '🍏')}</h1>
                        <h2 style="margin:0; color: white;">{selected_food.get('status', 'Analyzing...')}</h2>
                        <h3 style="margin:0; color: white;">Health Score: {selected_food.get('score', 0)}/100</h3>
                    </div>
                """, unsafe_allow_html=True)

                # Lấy và vẽ biểu đồ dinh dưỡng
                nut_df = get_raw_nutrients(fdc_id)
                col_chart, col_advice = st.columns([2, 1])
                with col_chart:
                    fig = px.bar(nut_df.sort_values('Amount', ascending=False).head(10), x='Amount', y='Nutrient',
                                 orientation='h', title="Nutrient Breakdown")
                    st.plotly_chart(fig, use_container_width=True)
                with col_advice:
                    st.info(L["advice_title"])
                    st.markdown(
                        f"<div class='ai-box'><b>Scientific Guidance:</b> {selected_food.get('description')} is evaluated as {selected_food.get('status')}.</div>",
                        unsafe_allow_html=True)

    # --- TAB 2: ELITE FOODS LAB (KHÔI PHỤC ADMIN & COMMENTS) ---
    with tab2:
        st.header(L["tab2"])
        # A. Admin Panel
        with st.expander(L["admin_title"]):
            with st.form("admin_post"):
                t = st.text_input("Food Name / Title")
                c = st.text_area("Detailed Analysis")
                img = st.text_input("Image URL")
                if st.form_submit_button("Publish Article"):
                    articles_col.insert_one(
                        {"title": t, "content": c, "image": img, "date": datetime.now(), "comments": []})
                    st.success("Published!");
                    st.rerun()

        # B. Danh sách bài viết & Thảo luận
        articles = list(articles_col.find().sort("date", -1))
        for art in articles:
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(art.get('image', 'https://via.placeholder.com/150'))
                with col2:
                    st.subheader(art['title'])
                    st.write(art['content'])
                    # Hiển thị Comments
                    with st.expander(f"{L['comment_section']} ({len(art.get('comments', []))})"):
                        for cmt in art.get('comments', []):
                            st.caption(f"👤 {cmt['author']} | 📅 {cmt['time']}")
                            st.write(cmt['text'])
                        # Form gửi comment
                        with st.form(f"cmt_{art['_id']}", clear_on_submit=True):
                            name = st.text_input("Name")
                            msg = st.text_area("Comment")
                            if st.form_submit_button(L["post_btn"]):
                                articles_col.update_one({"_id": art["_id"]}, {"$push": {
                                    "comments": {"author": name or "Anon", "text": msg,
                                                 "time": datetime.now().strftime("%Y-%m-%d")}}})
                                st.rerun()

    with tab3:
        st.header("Project Overview")
        st.info("System optimized for Environmental Toxicology and Nutritional Research by Trung Nguyen.")

# --- 8. CHATBOT HIỆN ĐẠI (AVATAR CLICK) ---
st.divider()
col_bot, _ = st.columns([1, 5])
with col_bot:
    # Nút bong bóng có hình bác sĩ
    st.markdown(f"**{L['chat_label']}**")
    if st.button("💬 Open AI Assistant", key="chat_btn"):
        st.session_state.show_chat = not st.session_state.get('show_chat', False)

if st.session_state.get('show_chat'):
    with st.container():
        # Hiển thị avatar bác sĩ trong khung chat
        st.image(DOCTOR_AVATAR, width=100)
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"], avatar=DOCTOR_AVATAR if m["role"] == "assistant" else None):
                st.markdown(m["content"])
        if p := st.chat_input("..."):
            st.session_state.messages.append({"role": "user", "content": p})
            with st.chat_message("user"): st.markdown(p)
            resp = model.generate_content(L["chat_role"] + p)
            st.session_state.messages.append({"role": "assistant", "content": resp.text})
            st.rerun()

# --- 9. FOOTER ---
st.markdown(f"<br><hr><center>{L['footer']}</center>", unsafe_allow_html=True)