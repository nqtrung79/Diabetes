import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from datetime import datetime
import time
import requests
import google.generativeai as genai

# --- 1. CẤU HÌNH TRANG & GOOGLE AI ---
st.set_page_config(page_title="Diabetes Research Factory", layout="wide")

# Cấu hình Gemini (Thay API Key của anh vào đây)
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
        "chat_role": "You are a diabetes expert. Answer scientifically and concisely: ",
        "footer": "© Data source: USDA's Food Composition",
        "auth_title": "🔑 Account",
        "login": "Login",
        "register": "Register"
    },
    "Tiếng Việt": {
        "flag": "🇻🇳",
        "title": "🛡️ Giải mã Thực phẩm, Đẩy lùi Tiểu đường",
        "tab1": "🍏 Trí tuệ Thực phẩm USDA",
        "tab2": "🛡️ Phòng thí nghiệm Elite",
        "tab3": "📄 Về dự án",
        "chat_placeholder": "Hỏi bác sĩ AI (VD: Tôi có nên ăn sầu riêng không?)",
        "chat_role": "Bạn là một chuyên gia về bệnh tiểu đường. Hãy trả lời khoa học và dễ hiểu: ",
        "footer": "© Nguồn dữ liệu: Thành phần thực phẩm của USDA",
        "auth_title": "🔑 Tài khoản",
        "login": "Đăng nhập",
        "register": "Đăng ký"
    }
}

# --- 3. SIDEBAR: CHỌN NGÔN NGỮ & AUTH ---
with st.sidebar:
    st.title("🛡️ Research Factory")

    # Chọn ngôn ngữ bằng Radio hoặc Selectbox với hình ảnh cờ
    selected_lang_name = st.radio(
        "Language / Ngôn ngữ",
        options=["Tiếng Việt", "English"],
        format_func=lambda x: f"{LANGUAGES[x]['flag']} {x}",
        horizontal=True
    )
    L = LANGUAGES[selected_lang_name]

    st.divider()

    # Logic Đăng nhập / Đăng ký
    if 'user_email' not in st.session_state:
        st.subheader(L["auth_title"])
        auth_tab1, auth_tab2 = st.tabs([L["login"], L["register"]])

        with auth_tab1:
            email = st.text_input("Email", key="l_email")
            pw = st.text_input("Password", type="password", key="l_pw")
            if st.button(L["login"], use_container_width=True):
                st.session_state.user_email = email
                st.rerun()

        with auth_tab2:
            if st.button(L["register"], use_container_width=True):
                st.session_state.step = "REGISTER_FORM"
                st.rerun()
    else:
        st.success(f"👤 {st.session_state.user_email}")
        if st.button("Logout / Đăng xuất"):
            del st.session_state.user_email
            st.rerun()


# --- 4. KẾT NỐI DATABASE (Dùng chung cho toàn app) ---
@st.cache_resource
def init_connection():
    client = MongoClient(st.secrets["MONGO_URI"])
    return client


client = init_connection()
db = client["USDA_Healthy_Food"]  # Hoặc "Foodata" tùy database của anh
articles_col = db['food_articles']

# --- 5. GIAO DIỆN CHÍNH ---
st.title(L["title"])

# Hiển thị Form Đăng ký nếu người dùng chọn
if st.session_state.get('step') == "REGISTER_FORM":
    st.header(L["register"])
    with st.form("reg_form"):
        st.text_input("Họ và Tên*")
        st.text_input("Email*")
        st.text_input("Mật khẩu*", type="password")
        if st.form_submit_button("✅ Submit"):
            st.session_state.step = "HOME"
            st.success("Success!")
            st.rerun()
    if st.button("Back"):
        st.session_state.step = "HOME"
        st.rerun()

else:
    tab1, tab2, tab3 = st.tabs([L["tab1"], L["tab2"], L["tab3"]])

    with tab1:
        st.info("Nội dung USDA Explorer sẽ hiển thị ở đây (Giữ nguyên code cũ của anh)")
        # Anh copy code của Tab Explorer vào đây...

    with tab2:
        st.header(L["tab2"])
        # Logic Admin & Grid bài viết
        # Chèn phần elite_foods_lab() của anh vào đây

    with tab3:
        st.write(L["tab3"])

# --- 6. CHATBOT AI (Floating Style với hình đại diện) ---
st.divider()
st.subheader(f"🤖 {L['chat_placeholder']}")

# Container cho nội dung chat
chat_container = st.container()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Avatar bác sĩ nữ (Link ảnh minh họa)
AVATAR_URL = "https://cdn-icons-png.flaticon.com/512/3304/3304567.png"

for message in st.session_state.messages:
    with chat_container.chat_message(message["role"], avatar=AVATAR_URL if message["role"] == "assistant" else None):
        st.markdown(message["content"])

if prompt := st.chat_input(L["chat_placeholder"]):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container.chat_message("user"):
        st.markdown(prompt)

    with chat_container.chat_message("assistant", avatar=AVATAR_URL):
        full_prompt = L["chat_role"] + prompt
        try:
            response = model.generate_content(full_prompt)
            answer = response.text
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except:
            st.error("AI Error. Please check API Key.")

# --- 7. FOOTER (Đảm bảo hiển thị dưới cùng) ---
st.markdown("---")
st.markdown(
    f"<div style='text-align:center; color:gray; padding-bottom:20px;'>{L['footer']}</div>",
    unsafe_allow_html=True
)