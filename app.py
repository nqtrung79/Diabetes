import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import google.generativeai as genai
from datetime import datetime
import time
import requests

# --- 1. CONFIG & CẤU HÌNH AI ---
st.set_page_config(page_title="Diabetes Research Factory", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')

# --- 2. TỪ ĐIỂN ĐA NGÔN NGỮ ---
LANGUAGES = {
    "English": {
        "flag": "🇺🇸",
        "title": "🛡️ Decoding Food, Defeating Diabetes",
        "tab1": "🍏 USDA Food Intelligence",
        "tab2": "🛡️ Elite Foods Lab",
        "tab3": "📄 About Project",
        "chat_placeholder": "Ask our AI Doctor (e.g., Can I eat Durian?)",
        "chat_role": "You are a diabetes expert. Answer scientifically: ",
        "auth_title": "🔑 Account",
        "login": "Login",
        "register": "Register",
        "search_label": "🔍 Search food name",
        "comment_section": "💬 Discussion",
        "post_btn": "Post Comment"
    },
    "Tiếng Việt": {
        "flag": "🇻🇳",
        "title": "🛡️ Giải mã Thực phẩm, Đẩy lùi Tiểu đường",
        "tab1": "🍏 Trí tuệ Thực phẩm USDA",
        "tab2": "🛡️ Phòng thí nghiệm Elite",
        "tab3": "📄 Về dự án",
        "chat_placeholder": "Hỏi bác sĩ AI (VD: Tôi có nên ăn sầu riêng không?)",
        "chat_role": "Bạn là một chuyên gia về bệnh tiểu đường. Hãy trả lời khoa học: ",
        "auth_title": "🔑 Tài khoản",
        "login": "Đăng nhập",
        "register": "Đăng ký",
        "search_label": "🔍 Tìm tên thực phẩm",
        "comment_section": "💬 Thảo luận",
        "post_btn": "Gửi bình luận"
    }
}

# --- 3. DATABASE & WEBHOOK LOGIC ---
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["USDA_Healthy_Food"]
articles_col = db['food_articles']


def send_to_webhook(data):
    WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", "")
    try:
        requests.post(WEBHOOK_URL, json=data, timeout=5)
    except:
        pass


def is_spam(comment_text):
    bad_words = ['http', 'https', 'www', 'buy now', 'cờ bạc', 'quảng cáo']
    return any(word in comment_text.lower() for word in bad_words) or len(comment_text) < 3


# --- 4. SIDEBAR: CHỌN NGÔN NGỮ & AUTH (Sử dụng Webhook) ---
with st.sidebar:
    st.title("🛡️ Research Factory")

    selected_lang = st.radio("Language", options=["Tiếng Việt", "English"],
                             format_func=lambda x: f"{LANGUAGES[x]['flag']} {x}", horizontal=True)
    L = LANGUAGES[selected_lang]
    st.divider()

    if 'user_email' not in st.session_state:
        st.subheader(L["auth_title"])
        auth_tab1, auth_tab2 = st.tabs([L["login"], L["register"]])
        with auth_tab1:
            email = st.text_input("Email", key="l_email")
            if st.button(L["login"], use_container_width=True):
                send_to_webhook({"action": "LOGIN", "email": email})
                st.session_state.user_email = email
                st.rerun()
        with auth_tab2:
            if st.button(L["register"], use_container_width=True):
                st.session_state.step = "REGISTER_FORM"
                st.rerun()
    else:
        st.success(f"👤 {st.session_state.user_email}")
        if st.button("Logout"):
            del st.session_state.user_email
            st.rerun()

# --- 5. GIAO DIỆN CHÍNH ---
st.title(L["title"])

if st.session_state.get('step') == "REGISTER_FORM":
    # --- FORM ĐĂNG KÝ CHI TIẾT (Khôi phục từ code cũ của anh) ---
    st.header(L["register"])
    with st.form("full_reg"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Họ và Tên*")
        email = c1.text_input("Email đăng ký*")
        uni = c2.text_input("Đại học/Viện*")
        pw = st.text_input("Mật khẩu*", type="password")
        if st.form_submit_button("✅ Register"):
            send_to_webhook({"action": "REGISTER", "full_name": name, "email": email, "uni": uni})
            st.session_state.user_email = email
            st.session_state.step = "HOME"
            st.rerun()

else:
    tab1, tab2, tab3 = st.tabs([L["tab1"], L["tab2"], L["tab3"]])

    with tab1:
        # --- USDA EXPLORER ---
        search_input = st.text_input(L["search_label"], key="usda_search")
        # Giả lập logic query từ code cũ của anh
        query = {"description": {"$regex": search_input, "$options": "i"}} if search_input else {}
        scored_data = list(db.Scored_Foods.find(query).limit(10))

        if scored_data:
            df_view = pd.DataFrame(scored_data)[["icon", "description", "score", "status"]]
            st.dataframe(df_view, use_container_width=True)

            # Đặt nguồn ngay dưới bảng dữ liệu theo yêu cầu của anh
            st.markdown("<p style='color:gray; font-size: 0.8rem;'>© Data source: USDA's Food Composition</p>",
                        unsafe_allow_html=True)

    with tab2:
        # --- ELITE FOODS LAB (Admin + Grid + Comments) ---
        articles = list(articles_col.find().sort("date", -1))
        cols = st.columns(3)
        for idx, art in enumerate(articles):
            with cols[idx % 3]:
                st.image(art.get('image', 'https://via.placeholder.com/300'), use_container_width=True)
                st.subheader(art['title'])
                if st.button(f"Details: {art['title']}", key=f"art_{idx}"):
                    st.session_state.selected_article_id = art['_id']

        # --- CHI TIẾT BÀI VIẾT & COMMENT ---
        if 'selected_article_id' in st.session_state:
            st.divider()
            art_detail = articles_col.find_one({"_id": st.session_state.selected_article_id})
            if art_detail:
                st.header(art_detail['title'])
                st.write(art_detail['content'])

                # PHẦN THẢO LUẬN (Khôi phục logic comment)
                st.subheader(L["comment_section"])
                for cmt in art_detail.get('comments', []):
                    with st.chat_message("user"):
                        st.write(f"**{cmt['author']}**: {cmt['text']}")

                with st.form("cmt_form", clear_on_submit=True):
                    c_user = st.text_input("Name")
                    c_msg = st.text_area("Message")
                    if st.form_submit_button(L["post_btn"]):
                        if not is_spam(c_msg):
                            new_cmt = {"author": c_user or "Anon", "text": c_msg, "time": datetime.now()}
                            articles_col.update_one({"_id": art_detail['_id']}, {"$push": {"comments": new_cmt}})
                            st.rerun()

# --- 6. CHATBOT AI CỐ ĐỊNH (Hình đại diện Bác sĩ) ---
st.divider()
DOCTOR_AVATAR = "https://cdn-icons-png.flaticon.com/512/387/387561.png"

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=DOCTOR_AVATAR if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

if prompt := st.chat_input(L["chat_placeholder"]):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=DOCTOR_AVATAR):
        try:
            full_prompt = L["chat_role"] + prompt
            response = model.generate_content(full_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except:
            st.write("AI is connecting...")

# --- 7. FOOTER CHUẨN ---
st.markdown("<br><br><hr><center>© 2026 Young Scientist Supporter | Research Intelligence</center>",
            unsafe_allow_html=True)