import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import time

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Diabetes Research Factory", layout="wide")

# --- 2. TỪ ĐIỂN ĐA NGÔN NGỮ (DICTIONARY) ---
# Anh có thể dễ dàng thêm từ khóa mới vào đây
LANGUAGES = {
    "Tiếng Việt": {
        "flag": "🇻🇳",
        "title": "🛡️ Giải mã Thực phẩm, Đẩy lùi Tiểu đường",
        "tab1": "🍏 Trí tuệ Thực phẩm USDA",
        "tab2": "🛡️ Phòng thí nghiệm Elite",
        "tab3": "📄 Về dự án",
        "search_placeholder": "🔍 Tìm tên thực phẩm (VD: Yến mạch, Bông cải)...",
        "admin_title": "🛠️ Quản lý nội dung (Admin)",
        "food_name": "Tên thực phẩm",
        "category": "Nhóm",
        "content": "Nội dung chi tiết",
        "publish_btn": "Xuất bản bài viết",
        "read_more": "Xem chi tiết",
        "discussion": "💬 Thảo luận",
        "comment_btn": "Gửi bình luận",
        "name_label": "Tên của bạn",
        "comment_label": "Ý kiến của bạn"
    },
    "English": {
        "flag": "🇺🇸",
        "title": "🛡️ Decoding Food, Defeating Diabetes",
        "tab1": "🍏 USDA Food Intelligence",
        "tab2": "🛡️ Elite Foods Lab",
        "tab3": "📄 About Project",
        "search_placeholder": "🔍 Search food name (e.g., Oats, Broccoli)...",
        "admin_title": "🛠️ Content Management (Admin)",
        "food_name": "Food Name",
        "category": "Category",
        "content": "Detailed Analysis",
        "publish_btn": "Publish Article",
        "read_more": "Read Details",
        "discussion": "💬 Discussion",
        "comment_btn": "Post Comment",
        "name_label": "Your Name",
        "comment_label": "Your message"
    }
}

# --- 3. KHỞI TẠO NGÔN NGỮ TRONG SESSION STATE ---
if 'lang' not in st.session_state:
    st.session_state.lang = "Tiếng Việt"  # Mặc định tiếng Việt

# --- 4. SIDEBAR: CHỌN NGÔN NGỮ VỚI LÁ CỜ ---
with st.sidebar:
    st.title("🌐 Ngôn ngữ / Language")

    # Tạo 2 cột để đặt 2 lá cờ nằm ngang
    col_vn, col_us = st.columns(2)

    with col_vn:
        if st.button("🇻🇳 Tiếng Việt", use_container_width=True):
            st.session_state.lang = "Tiếng Việt"
            st.rerun()

    with col_us:
        if st.button("🇺🇸 English", use_container_width=True):
            st.session_state.lang = "English"
            st.rerun()

    st.divider()
    st.write(f"Đang sử dụng: **{st.session_state.lang}**")

# Gán từ điển đang chọn vào biến L để dùng cho ngắn gọn
L = LANGUAGES[st.session_state.lang]

# --- 5. GIAO DIỆN CHÍNH (SỬ DỤNG BIẾN L) ---
st.title(L["title"])

tab1, tab2, tab3 = st.tabs([L["tab1"], L["tab2"], L["tab3"]])

with tab1:
    search_input = st.text_input(L["search_placeholder"], key="usda_search")
    # ... (Giữ nguyên logic xử lý dữ liệu USDA của anh)

with tab2:
    st.header(f"🔬 {L['tab2']}")

    # Giao diện Admin đã dịch
    with st.expander(L["admin_title"]):
        with st.form("admin_form"):
            new_title = st.text_input(L["food_name"])
            new_cat = st.selectbox(L["category"], ["Beans", "Nuts", "Seeds", "Greens"])
            new_content = st.text_area(L["content"])
            if st.form_submit_button(L["publish_btn"]):
                # Logic insert MongoDB của anh ở đây
                st.success("Success!")

    # Ví dụ nút xem chi tiết đã dịch
    if st.button(L["read_more"], key="example_btn"):
        st.write("Chi tiết nội dung...")

    st.subheader(L["discussion"])
    # Form comment đã dịch
    with st.form("cmt_form"):
        u_name = st.text_input(L["name_label"])
        u_msg = st.text_area(L["comment_label"])
        if st.form_submit_button(L["comment_btn"]):
            st.info("Processing...")

with tab3:
    st.write("Thông tin dự án / Project Info")