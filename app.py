import streamlit as st
import pandas as pd
from pymongo import MongoClient
import google.generativeai as genai
from datetime import datetime
import time

# --- 1. CẤU HÌNH TRANG (PHẢI LÀ DÒNG ĐẦU TIÊN) ---
st.set_page_config(page_title="Diabetes Research Factory", layout="wide")

# --- 2. TỪ ĐIỂN ĐA NGÔN NGỮ ---
LANGUAGES = {
    "English": {
        "flag": "🇺🇸",
        "title": "🛡️ Decoding Food, Defeating Diabetes",
        "tab1": "🍏 USDA Food Intelligence",
        "tab2": "🛡️ Elite Foods Lab",
        "tab3": "📄 About Project",
        "chat_placeholder": "Ask our AI Doctor...",
        "chat_role": "You are a diabetes expert. Answer scientifically: ",
        "footer": "© Data source: USDA's Food Composition",
        "login": "Login",
        "register": "Register"
    },
    "Tiếng Việt": {
        "flag": "🇻🇳",
        "title": "🛡️ Giải mã Thực phẩm, Đẩy lùi Tiểu đường",
        "tab1": "🍏 Trí tuệ Thực phẩm USDA",
        "tab2": "🛡️ Phòng thí nghiệm Elite",
        "tab3": "📄 Về dự án",
        "chat_placeholder": "Hỏi bác sĩ AI của bạn...",
        "chat_role": "Bạn là một chuyên gia về bệnh tiểu đường. Hãy trả lời khoa học: ",
        "footer": "© Nguồn dữ liệu: Thành phần thực phẩm của USDA",
        "login": "Đăng nhập",
        "register": "Đăng ký"
    }
}

# --- 3. SIDEBAR (LUÔN HIỂN THỊ) ---
with st.sidebar:
    st.title("🛡️ Research Factory")

    # Lựa chọn ngôn ngữ với hình ảnh lá cờ
    selected_lang = st.radio(
        "Language / Ngôn ngữ",
        options=["Tiếng Việt", "English"],
        format_func=lambda x: f"{LANGUAGES[x]['flag']} {x}",
        horizontal=True
    )
    L = LANGUAGES[selected_lang]

    st.divider()

    # Logic Tài khoản
    if 'user_email' not in st.session_state:
        st.subheader("🔑 " + L["login"])
        t1, t2 = st.tabs([L["login"], L["register"]])
        with t1:
            email = st.text_input("Email", key="login_email")
            if st.button("OK", use_container_width=True):
                st.session_state.user_email = email
                st.rerun()
        with t2:
            if st.button(L["register"], use_container_width=True):
                st.session_state.step = "REGISTER"
                st.rerun()
    else:
        st.success(f"👤 {st.session_state.user_email}")
        if st.button("Logout"):
            del st.session_state.user_email
            st.rerun()

# --- 4. GIAO DIỆN CHÍNH ---
st.title(L["title"])

# Kiểm tra nếu đang ở trang đăng ký
if st.session_state.get('step') == "REGISTER":
    st.header(L["register"])
    # (Chèn form đăng ký của anh vào đây)
    if st.button("⬅️ Back"):
        st.session_state.step = "HOME"
        st.rerun()
else:
    # HIỂN THỊ TABS
    tab1, tab2, tab3 = st.tabs([L["tab1"], L["tab2"], L["tab3"]])

    with tab1:
        st.subheader(L["tab1"])
        # Code USDA Explorer của anh đặt ở đây

    with tab2:
        st.subheader(L["tab2"])
        # Code Elite Foods Lab đặt ở đây

    with tab3:
        st.write(L["tab3"])

# --- 5. CHATBOT AVATAR (LUÔN Ở DƯỚI TABS) ---
st.divider()
st.markdown(f"### 👩‍⚕️ AI Assistant")

# Đường dẫn ảnh bác sĩ tư vấn
DOCTOR_AVATAR = "https://cdn-icons-png.flaticon.com/512/387/387561.png"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    avatar = DOCTOR_AVATAR if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Ô nhập liệu chat
if prompt := st.chat_input(L["chat_placeholder"]):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Giả lập phản hồi AI (Anh hãy kết nối API Gemini ở đây)
    with st.chat_message("assistant", avatar=DOCTOR_AVATAR):
        response_text = f"Đây là phản hồi từ chuyên gia bằng {selected_lang}..."
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})

# --- 6. FOOTER (PHẢI Ở CUỐI CÙNG FILE) ---
st.markdown("<br><br>", unsafe_allow_html=True)  # Tạo khoảng cách
st.markdown(
    f"<div style='text-align:center; color:gray; border-top: 1px solid #eee; padding-top:20px;'>{L['footer']}</div>",
    unsafe_allow_html=True
)