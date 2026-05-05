import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import google.generativeai as genai
from datetime import datetime
import time
import requests

# --- 1. CẤU HÌNH TRANG & ICON ---
st.set_page_config(page_title="Diabetes Research Factory", layout="wide")

# --- 2. HÌNH ẢNH & BIẾN CỐ ĐỊNH ---
# ANH THAY LINK ẢNH BÁC SỸ ĐẸP CỦA ANH VÀO ĐÂY
DOCTOR_AVATAR = "https://cdn-icons-png.flaticon.com/512/3304/3304567.png"

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
        "chat_prompt": "You need diabetes advice?",
        "chat_role": "You are a diabetes expert. Answer scientifically: ",
        "auth_title": "🔑 Account",
        "login": "Login",
        "register": "Register",
        "admin_title": "🛠️ Content Management (Admin)",
        "comment_section": "💬 Discussion"
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
        "chat_prompt": "Bạn cần tư vấn hỗ trợ tiểu đường?",
        "chat_role": "Bạn là một chuyên gia về bệnh tiểu đường. Hãy trả lời khoa học: ",
        "auth_title": "🔑 Tài khoản",
        "login": "Đăng nhập",
        "register": "Đăng ký",
        "admin_title": "🛠️ Quản lý nội dung (Admin)",
        "comment_section": "💬 Thảo luận"
    }
}

# --- 4. CUSTOM CSS (Giao diện hiện đại) ---
st.markdown(f"""
<style>
    .nutrient-card {{ background-color: #f8f9fa; border-radius: 10px; padding: 10px; border: 1px solid #dee2e6; text-align: center; }}
    .nutrient-value {{ font-size: 16px; font-weight: bold; color: #2e7d32; }}
    .score-container {{ padding: 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px; }}
    .article-card {{ border: 1px solid #eee; padding: 15px; border-radius: 10px; background: white; height: 100%; }}
    /* Floating Chatbot Button */
    .stChatFloating {{ position: fixed; bottom: 20px; right: 20px; z-index: 99; }}
</style>
""", unsafe_allow_html=True)

# --- 5. KẾT NỐI DATABASE & HÀM BỔ TRỢ ---
client = MongoClient(st.secrets["MONGO_URI"])
db = client["USDA_Healthy_Food"]
articles_col = db['food_articles']

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')


def send_to_webhook(data):
    try:
        requests.post(st.secrets["WEBHOOK_URL"], json=data, timeout=5)
    except:
        pass


def is_spam(text):
    bad_words = ['http', 'www', 'cờ bạc', 'quảng cáo', 'mua hàng']
    return any(w in text.lower() for w in bad_words) or len(text) < 3


@st.cache_data
def get_raw_nutrients(fdc_id):
    pipeline = [{"$match": {"fdc_id": int(fdc_id)}}, {
        "$lookup": {"from": "Nutrient_Definitions", "localField": "nutrient_id", "foreignField": "id",
                    "as": "details"}}, {"$unwind": "$details"}]
    results = list(db.Core_Nutrients.aggregate(pipeline))
    return pd.DataFrame(
        [{"Nutrient": r['details']['name'], "Amount": r['amount'], "Unit": r['details']['unit_name']} for r in results])


# --- 6. SIDEBAR: NGÔN NGỮ & AUTH ---
with st.sidebar:
    st.title("🛡️ Research Factory")

    # CHỌN NGÔN NGỮ QUA LÁ CỜ
    st.write("🌐 **Language / Ngôn ngữ**")
    col_v, col_e = st.columns(2)
    if col_v.button("🇻🇳 Tiếng Việt"): st.session_state.lang = "Tiếng Việt"
    if col_e.button("🇺🇸 English"): st.session_state.lang = "English"

    selected_lang = st.session_state.get('lang', "Tiếng Việt")
    L = LANGUAGES[selected_lang]

    st.divider()

    # HỆ THỐNG ĐĂNG NHẬP/ĐĂNG KÝ
    if 'user_email' not in st.session_state:
        st.subheader(L["auth_title"])
        auth_tab1, auth_tab2 = st.tabs([L["login"], L["register"]])
        with auth_tab1:
            em = st.text_input("Email", key="l_em")
            pw = st.text_input("Pass", type="password", key="l_pw")
            if st.button(L["login"], use_container_width=True):
                send_to_webhook({"action": "LOGIN", "email": em})
                st.session_state.user_email = em
                st.rerun()
        with auth_tab2:
            if st.button("🚀 " + L["register"], use_container_width=True):
                st.session_state.step = "DANG_KY_FORM"
                st.rerun()
    else:
        st.success(f"👤 {st.session_state.user_email}")
        if st.button("Đăng xuất"):
            del st.session_state.user_email
            st.rerun()

    st.caption("© 2026 Young Scientist Supporter")

# --- 7. MÀN HÌNH ĐĂNG KÝ CHI TIẾT ---
if st.session_state.get('step') == "DANG_KY_FORM":
    st.header("📝 " + L["register"])
    with st.form("reg_form"):
        c1, c2 = st.columns(2)
        fn = c1.text_input("Họ và Tên*")
        em = c1.text_input("Email*")
        un = c2.text_input("Viện/Trường*")
        pw = st.text_input("Mật khẩu*", type="password")
        bio = st.text_area("Hướng nghiên cứu")
        if st.form_submit_button("✅ Hoàn tất"):
            send_to_webhook({"action": "REGISTER", "full_name": fn, "email": em, "uni": un, "bio": bio})
            st.session_state.user_email = em
            st.session_state.step = "HOME"
            st.rerun()
    if st.button("⬅️ Quay lại"): st.session_state.step = "HOME"; st.rerun()

# --- 8. GIAO DIỆN CHÍNH ---
else:
    st.title(L["title"])
    t1, t2, t3 = st.tabs([L["tab1"], L["tab2"], L["tab3"]])

    # --- TAB 1: USDA EXPLORER (Tính toán & Click) ---
    with t1:
        search = st.text_input(L["search_label"], key="main_search")
        query = {"description": {"$regex": search, "$options": "i"}} if search else {}
        scored_data = list(db.Scored_Foods.find(query).sort("score", -1).limit(15))

        if scored_data:
            df_view = pd.DataFrame(scored_data)[["description"]]
            df_view.columns = [L["food_type"]]
            event = st.dataframe(df_view, use_container_width=True, on_select="rerun", selection_mode="single-row",
                                 hide_index=True)
            st.markdown(f"<p style='color:gray; font-size:0.8rem'>{L['source']}</p>", unsafe_allow_html=True)

            if len(event.selection.rows) > 0:
                item = scored_data[event.selection.rows[0]]
                # Score Card
                color_map = {1: "#1b5e20", 2: "#2e7d32", 3: "#f9a825", 4: "#ef6c00", 5: "#c62828", 6: "#8e0000"}
                st.markdown(f"""<div class="score-container" style="background:{color_map.get(item['rank'], '#757575')}">
                    <h1>{item['icon']} {item['status']}</h1>
                    <h3>Score: {item['score']}/100</h3>
                </div>""", unsafe_allow_html=True)

                # Nutrients & Plotly
                nut_df = get_raw_nutrients(item['fdc_id'])
                c_chart, c_cards = st.columns([2, 1])
                with c_chart:
                    fig = px.bar(nut_df.head(10), x='Amount', y='Nutrient', orientation='h', title="Nutrients")
                    st.plotly_chart(fig, use_container_width=True)
                with c_cards:
                    st.info(L["advice_title"])
                    st.write(item['description'])

    # --- TAB 2: ELITE LAB (Admin & Articles) ---
    with t2:
        with st.expander(L["admin_title"]):
            with st.form("admin_form"):
                at = st.text_input("Tên thực phẩm")
                ac = st.selectbox("Nhóm", ["Beans", "Nuts", "Seeds", "Greens"])
                ai = st.text_input("Link ảnh")
                atxt = st.text_area("Nội dung khoa học")
                if st.form_submit_button("Publish"):
                    articles_col.insert_one(
                        {"title": at, "category": ac, "image": ai, "content": atxt, "date": datetime.now(),
                         "comments": []})
                    st.rerun()

        articles = list(articles_col.find().sort("date", -1))
        cols = st.columns(3)
        for idx, art in enumerate(articles):
            with cols[idx % 3]:
                st.image(art.get('image') or "https://via.placeholder.com/300", use_container_width=True)
                st.subheader(art['title'])
                if st.button(f"Xem chi tiết", key=f"art_{art['_id']}"):
                    st.session_state.selected_art = art['_id']

        if 'selected_art' in st.session_state:
            curr_art = articles_col.find_one({"_id": st.session_state.selected_art})
            if curr_art:
                st.divider()
                st.header(curr_art['title'])
                st.write(curr_art['content'])

                # HỆ THỐNG COMMENT TÍCH HỢP
                st.subheader(L["comment_section"])
                for c in curr_art.get('comments', []):
                    with st.chat_message("user"): st.write(f"**{c['user']}**: {c['text']} ({c['time']})")

                with st.form("cmt_form", clear_on_submit=True):
                    u_n = st.text_input("Tên")
                    u_m = st.text_area("Ý kiến")
                    if st.form_submit_button("Gửi"):
                        if not is_spam(u_m):
                            articles_col.update_one({"_id": curr_art["_id"]}, {"$push": {
                                "comments": {"user": u_n or "Anon", "text": u_m,
                                             "time": datetime.now().strftime("%Y-%m-%d %H:%M")}}})
                            st.rerun()
                if st.button("✖ Đóng"): del st.session_state.selected_art; st.rerun()

    with t3:
        st.write("Research by Thao Thanh Nguyen - IET 2026")

# --- 9. CHATBOT BÁC SỸ TƯ VẤN (Bong bóng phía dưới) ---
st.divider()
st.markdown("### 🤖 Trợ lý AI")
c_bot, c_txt = st.columns([1, 4])
with c_bot:
    st.image(DOCTOR_AVATAR, width=100)
    st.caption(L["chat_prompt"])

with c_txt:
    user_q = st.text_input(L["chat_prompt"], key="bot_q", label_visibility="collapsed",
                           placeholder="Hỏi bác sĩ ngay...")
    if user_q:
        with st.spinner("Đang suy nghĩ..."):
            resp = model.generate_content(L["chat_role"] + user_q).text
            st.markdown(f"""<div style="background:#f0f7ff; padding:15px; border-radius:10px; border-left:5px solid #2e7d32">
                <b>Bác sĩ AI:</b><br>{resp}</div>""", unsafe_allow_html=True)