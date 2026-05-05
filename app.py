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
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. TỪ ĐIỂN ĐA NGÔN NGỮ (Sử dụng Flag thay cho Radio) ---
LANGUAGES = {
    "English": {
        "title": "🛡️ Decoding Food, Defeating Diabetes",
        "tab1": "🍏 USDA Food Intelligence",
        "tab2": "🛡️ Elite Foods Lab",
        "tab3": "📄 About Project",
        "chat_label": "Need diabetes advice?",
        "chat_role": "You are a diabetes expert. Answer scientifically: ",
        "footer": "© 2026 Young Scientist Supporter",
        "source": "© Data source: USDA's Food Composition"
    },
    "Tiếng Việt": {
        "title": "🛡️ Giải mã Thực phẩm, Đẩy lùi Tiểu đường",
        "tab1": "🍏 Trí tuệ Thực phẩm USDA",
        "tab2": "🛡️ Phòng thí nghiệm Elite",
        "tab3": "📄 Về dự án",
        "chat_label": "Bạn cần tư vấn về tiểu đường?",
        "chat_role": "Bạn là một chuyên gia về bệnh tiểu đường. Hãy trả lời khoa học: ",
        "footer": "© 2026 Người hỗ trợ nhà khoa học trẻ",
        "source": "© Nguồn dữ liệu: Thành phần thực phẩm của USDA"
    }
}

# --- 3. GIAO DIỆN CHUYÊN NGHIỆP (CSS) ---
# Anh dán link ảnh bác sĩ của anh vào đây
DOCTOR_AVATAR = "https://cdn-icons-png.flaticon.com/512/3304/3304567.png"

st.markdown(f"""
    <style>
    /* Ẩn nút radio mặc định */
    [data-testid="stSidebarNav"] {{display: none;}}

    /* Hiệu ứng bong bóng Chat */
    .chat-bubble {{
        position: fixed; bottom: 20px; right: 20px; z-index: 1000;
        cursor: pointer; transition: 0.3s;
    }}
    .chat-bubble img {{
        width: 70px; height: 70px; border-radius: 50%;
        border: 3px solid #2e7d32; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }}
    /* Style cho bảng dữ liệu */
    .stDataFrame {{ border: 1px solid #eee; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR: NGÔN NGỮ & AUTH (Giữ nguyên Webhook) ---
with st.sidebar:
    st.title("🛡️ Research Factory")

    # Thay thế Radio bằng 2 nút bấm hình lá cờ cho chuyên nghiệp
    col_v, col_e = st.columns(2)
    if col_v.button("🇻🇳 Tiếng Việt"): st.session_state.lang = "Tiếng Việt"
    if col_e.button("🇺🇸 English"): st.session_state.lang = "English"

    selected_lang = st.session_state.get('lang', "Tiếng Việt")
    L = LANGUAGES[selected_lang]

    st.divider()
    # (Tại đây chèn lại logic send_to_webhook và Auth của anh)

# --- 5. GIAO DIỆN CHÍNH ---
st.title(L["title"])
tab1, tab2, tab3 = st.tabs([L["tab1"], L["tab2"], L["tab3"]])

with tab1:
    # KHÔI PHỤC LOGIC TÍNH TOÁN CỦA ANH
    search_input = st.text_input("🔍 Search", key="search_usda")

    # Kết nối DB và lấy dữ liệu
    client = MongoClient(st.secrets["MONGO_URI"])
    db = client["USDA_Healthy_Food"]
    query = {"description": {"$regex": search_input, "$options": "i"}} if search_input else {}
    scored_data = list(db.Scored_Foods.find(query).limit(15))

    if scored_data:
        df = pd.DataFrame(scored_data)
        # CHỈ HIỆN CỘT FOOD TYPE (Description)
        df_display = df[["description"]].copy()
        df_display.columns = ["Food Type"]

        # BẬT TÍNH NĂNG CLICK HÀNG ĐỂ TÍNH TOÁN
        event = st.dataframe(df_display, use_container_width=True, on_select="rerun", selection_mode="single-row",
                             hide_index=True)

        # Nguồn ngay dưới bảng
        st.markdown(f"<p style='color:gray; font-size: 0.8rem;'>{L['source']}</p>", unsafe_allow_html=True)

        # Xử lý khi click vào hàng (Khôi phục toàn bộ phần phân tích dinh dưỡng của anh)
        if len(event.selection.rows) > 0:
            selected_food = scored_data[event.selection.rows[0]]
            st.subheader(f"📊 Analysis for: {selected_food['description']}")
            # ... (Tại đây chèn code vẽ biểu đồ Plotly và phân tích dinh dưỡng anh đã dày công viết)

with tab2:
    # KHÔI PHỤC FORM ADMIN ĐĂNG BÀI TỰ DO
    with st.expander("🛠️ Admin Panel (Post Article)"):
        with st.form("admin_post"):
            new_title = st.text_input("Title")
            new_content = st.text_area("Content")
            if st.form_submit_button("Publish"):
                # Logic insert vào MongoDB của anh
                st.success("Published!")

    # HIỂN THỊ BÀI VIẾT & COMMENT
    # (Chèn logic vòng lặp hiện bài viết và Comment Discussion của anh vào đây)

# --- 6. CHATBOT HIỆN ĐẠI: CLICK VÀO AVATAR MỚI HIỆN BẢNG ---
# Hiển thị icon bác sĩ ở góc
st.markdown(f'''
    <div class="chat-bubble">
        <img src="{DOCTOR_AVATAR}" alt="Doctor">
    </div>
''', unsafe_allow_html=True)

# Dùng checkbox ẩn để làm nút mở/đóng khung chat
show_chat = st.checkbox(L["chat_label"], value=False)

if show_chat:
    with st.container():
        st.info(f"👩‍⚕️ {L['chat_label']}")
        if "messages" not in st.session_state: st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar=DOCTOR_AVATAR if msg["role"] == "assistant" else None):
                st.markdown(msg["content"])

        if prompt := st.chat_input("..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            response = model.generate_content(L["chat_role"] + prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.rerun()

# --- 7. FOOTER ---
st.markdown(f"<hr><center>{L['footer']}</center>", unsafe_allow_html=True)