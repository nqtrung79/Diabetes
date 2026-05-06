import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import recipe_service as rs
from datetime import datetime
import time
import requests
import streamlit as st
import google.generativeai as genai
from groq import Groq



def send_to_webhook(data):
    try:
        # Anh cần thêm WEBHOOK_URL vào file secrets.toml
        webhook_url = st.secrets.get("WEBHOOK_URL")
        requests.post(webhook_url, json=data, timeout=5)
    except Exception as e:
        st.error(f"Lỗi gửi dữ liệu: {e}")

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Diabetes Research Factory", layout="wide")

# --- 2. TỪ ĐIỂN ĐA NGÔN NGỮ (DICTIONARY) ---
LANGUAGES = {
    "Tiếng Việt": {
        "title": "🛡️ Giải mã Thực phẩm, Đẩy lùi Tiểu đường",
        "tab1": "🍏 Trí tuệ Thực phẩm USDA",
        "tab2": "🛡️ Elite Foods Lab",
        "tab3": "📄 Về dự án",
        "search_label": "🔍 Tìm tên thực phẩm (VD: Yến mạch, Bông cải, Cá hồi)",
        "prev": "⬅️ Trang trước",
        "next": "Trang sau ➡️",
        "score_label": "Điểm sức khỏe Tiểu đường",
        "nut_title": "📊 Thành phần dinh dưỡng đầy đủ (Chuẩn USDA trên 100g)",
        "ai_title": "💡 Lời khuyên từ Chuyên gia AI",
        "scientific_summary": "🔬 Tóm tắt Khoa học",
        "dietary_guidance": "🌿 Hướng dẫn Chế độ ăn",
        "admin_title": "🛠️ Quản lý nội dung (Admin)",
        "publish_btn": "Xuất bản bài viết",
        "read_more": "Xem chi tiết",
        "discussion": "💬 Thảo luận",
        "comment_btn": "Gửi bình luận",
        "name_label": "Tên của bạn",
        "msg_label": "Ý kiến của bạn",
        "source": "© Nguồn dữ liệu: Thành phần thực phẩm của USDA",
        "register": "Đăng ký tài khoản nghiên cứu",
        "auth_header": "🔑 Tài khoản",
        "login_tab": "Đăng nhập",
        "register_tab": "Đăng ký",
        "email_label": "Email",
        "password_label": "Mật khẩu",
        "login_confirm": "Xác nhận Đăng nhập",
        "logout_btn": "Đăng xuất",
        "no_account": "Bạn chưa có tài khoản?",
        "create_account": "Tạo tài khoản mới"
    },
    "English": {
        "title": "🛡️ Decoding Food, Defeating Diabetes",
        "tab1": "🍏 USDA Food Intelligence",
        "tab2": "🛡️ Elite Foods Lab",
        "tab3": "📄 About Project",
        "search_label": "🔍 Search food name (e.g., Oats, Broccoli, Salmon)",
        "prev": "⬅️ Previous Page",
        "next": "Next Page ➡️",
        "score_label": "Diabetes Health Score",
        "nut_title": "📊 Full Nutrient Composition (USDA Standard per 100g)",
        "ai_title": "💡 AI Virtual Expert Advice",
        "scientific_summary": "🔬 Scientific Summary",
        "dietary_guidance": "🌿 Dietary Guidance",
        "admin_title": "🛠️ Content Management (Admin)",
        "publish_btn": "Publish Article",
        "read_more": "Read Details",
        "discussion": "💬 Discussion",
        "comment_btn": "Post Comment",
        "name_label": "Your Name",
        "msg_label": "Add to discussion",
        "source": "© Data source: USDA's Food Composition",
        "register": "Research Account Registration",
        "auth_header": "🔑 Account",
        "login_tab": "Login",
        "register_tab": "Register",
        "email_label": "Email",
        "password_label": "Password",
        "login_confirm": "Confirm Login",
        "logout_btn": "Logout",
        "no_account": "Don't have an account?",
        "create_account": "Create new account"
    }
}

# --- 3. CUSTOM CSS (Giữ nguyên thuật toán hiển thị của anh) ---
st.markdown("""
<style>
.nutrient-card { background-color: #f8f9fa; border-radius: 10px; padding: 15px; border: 1px solid #dee2e6; text-align: center; margin-bottom: 10px; min-height: 100px; }
.nutrient-value { font-size: 18px; font-weight: bold; color: #2e7d32; }
.nutrient-name { font-size: 13px; color: #616161; }
.score-container { padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; border: 2px solid #ddd; color: white; }
.ai-box { background-color: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 6px solid #007bff; color: #0d47a1; line-height: 1.6; }
.article-card { border: 1px solid #eee; padding: 15px; border-radius: 10px; background: white; transition: 0.3s; }
</style>
""", unsafe_allow_html=True)

# --- 4. DATABASE & SESSION STATE ---
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["USDA_Healthy_Food"]
articles_col = db['food_articles']

if 'lang' not in st.session_state: st.session_state.lang = "English"
L = LANGUAGES[st.session_state.lang]


def display_sidebar_auth():
    with st.sidebar:
        # 1. PHẦN CHỌN NGÔN NGỮ
        st.write("🌐 **Language / Ngôn ngữ**")
        c_us, c_vn = st.columns(2)  # Đưa English lên trước để ưu tiên
        if c_us.button("🇺🇸 English"): st.session_state.lang = "English"; st.rerun()
        if c_vn.button("🇻🇳 Tiếng Việt"): st.session_state.lang = "Tiếng Việt"; st.rerun()

        st.divider()
        st.title("🛡️ Diabetes Intelligence")

        # Lấy từ điển dựa trên ngôn ngữ đang chọn
        L = LANGUAGES.get(st.session_state.get('lang', 'English'), LANGUAGES['English'])

        # 2. KIỂM TRA ĐĂNG NHẬP
        if 'user_email' in st.session_state and st.session_state.user_email:
            st.success(f"👤 {st.session_state.user_email}")
            if st.button(L["logout_btn"]):  # Sửa từ "logout_btn" thành L["logout_btn"]
                for key in ["user_email", "step"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        else:
            st.subheader(L["auth_header"])  # Sửa thành biến L
            tab1, tab2 = st.tabs([L["login_tab"], L["register_tab"]])  # Sửa thành biến L

            with tab1:
                email = st.text_input(L["email_label"], key="login_email", placeholder="abc@email.com")
                # Sửa lỗi cú pháp: Thêm dấu đóng ngoặc kép cho "password_label"
                password = st.text_input(L["password_label"], type="password", key="login_pass")

                # Sửa thành L["login_confirm"] để hiển thị đúng ngôn ngữ
                if st.button(L["login_confirm"], use_container_width=True):
                    if email and password:
                        send_to_webhook({"action": "LOGIN", "email": email})
                        st.session_state.user_email = email
                        st.success("Signed in!")
                        st.rerun()
                    else:
                        st.error(
                            "Vui lòng nhập đủ thông tin." if st.session_state.lang == "Tiếng Việt" else "Please fill in all fields.")

            with tab2:
                st.write(L["no_account"])
                if st.button(L["create_account"], use_container_width=True):
                    st.session_state.step = "DANG_KY_FORM"
                    st.rerun()

        st.divider()
        st.caption("© 2026 Healthy Food")


# --- 5. LOGIC THUẬT TOÁN (ANTI-SPAM & FETCHING) ---
def is_spam(text):
    bad_words = ['http', 'https', 'www', 'buy now', 'cờ bạc', 'quảng cáo']
    return any(word in text.lower() for word in bad_words) or len(text) < 3


@st.cache_data
def get_raw_nutrients(fdc_id):
    pipeline = [{"$match": {"fdc_id": int(fdc_id)}}, {
        "$lookup": {"from": "Nutrient_Definitions", "localField": "nutrient_id", "foreignField": "id",
                    "as": "details"}}, {"$unwind": "$details"}]
    results = list(db.Core_Nutrients.aggregate(pipeline))
    return pd.DataFrame(
        [{"Nutrient": r['details']['name'], "Amount": r['amount'], "Unit": r['details']['unit_name']} for r in results])


# --- 6. SIDEBAR VỚI LÁ CỜ ---
# with st.sidebar:
    # st.title("🌐 Language")
    # c1, c2 = st.columns(2)
    # if c1.button("Tiếng Việt"): st.session_state.lang = "Tiếng Việt"; st.rerun()
    # if c2.button("English"): st.session_state.lang = "English"; st.rerun()
    # st.divider()
    # st.info(f"Phần mềm Nghiên cứu: {st.session_state.lang}")

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


# --- 8. ĐIỀU HƯỚNG GIAO DIỆN CHÍNH (MAIN NAVIGATION) ---
# Gọi Sidebar Auth trước để xử lý logic đăng nhập/ngôn ngữ
display_sidebar_auth()

# Lấy từ điển chuẩn theo ngôn ngữ đã chọn
L = LANGUAGES.get(st.session_state.get('lang', 'English'), LANGUAGES['English'])

# TRƯỜNG HỢP 1: MÀN HÌNH ĐĂNG KÝ CHI TIẾT
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
    if st.button("⬅️ Quay lại"):
        st.session_state.step = "HOME"
        st.rerun()

# TRƯỜNG HỢP 2: GIAO DIỆN CHÍNH (HOME)
else:
    st.title(L["title"])  # CHỈ GIỮ LẠI MỘT DÒNG TITLE DUY NHẤT Ở ĐÂY

    tab_explorer, tab_recommend, tab_about = st.tabs([L["tab1"], L["tab2"], L["tab3"]])

    # --- TAB 1: EXPLORER ---
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

            cp1, cp2, cp3 = st.columns([1, 2, 1])
            if cp1.button(L["prev"]): st.session_state.page = max(1, st.session_state.page - 1)
            if cp3.button(L["next"]): st.session_state.page += 1

            if len(event.selection.rows) > 0:
                selected_food = scored_data[event.selection.rows[0]]
                color_map = {1: "#1b5e20", 2: "#2e7d32", 3: "#f9a825", 4: "#ef6c00", 5: "#c62828", 6: "#8e0000"}
                bg_color = color_map.get(selected_food['rank'], "#757575")

                st.markdown(f'<div class="score-container" style="background-color: {bg_color};">'
                            f'<h1 style="font-size: 70px; margin:0;">{selected_food["icon"]}</h1>'
                            f'<h2>{selected_food["status"]}</h2>'
                            f'<h3>{L["score_label"]}: {selected_food["score"]}/100</h3></div>', unsafe_allow_html=True)

                nut_df = get_raw_nutrients(selected_food['fdc_id'])
                st.subheader(L["nut_title"])
                n_cols = st.columns(5)
                for idx, row in nut_df.iterrows():
                    with n_cols[idx % 5]:
                        st.markdown(f'<div class="nutrient-card"><div class="nutrient-name">{row["Nutrient"]}</div>'
                                    f'<div class="nutrient-value">{round(row["Amount"], 2)} <small>{row["Unit"]}</small></div></div>',
                                    unsafe_allow_html=True)

                advices = {
                    1: "Excellent choice!" if st.session_state.lang == "English" else "Lựa chọn tuyệt vời!",
                    2: "Safe for consumption." if st.session_state.lang == "English" else "An toàn sử dụng.",
                    3: "In moderation." if st.session_state.lang == "English" else "Dùng điều độ.",
                    4: "Caution." if st.session_state.lang == "English" else "Thận trọng.",
                    5: "Not recommended." if st.session_state.lang == "English" else "Không khuyến khích.",
                    6: "Danger Zone!" if st.session_state.lang == "English" else "Vùng nguy hiểm!"
                }

                st.markdown(f'<div class="ai-box"><b>{L["scientific_summary"]}:</b> {selected_food["status"]}.<br>'
                            f'<b>{L["dietary_guidance"]}:</b> {advices.get(selected_food["rank"])}</div>',
                            unsafe_allow_html=True)

                col_chart, col_recipe = st.columns([2, 1])
                with col_chart:
                    fig = px.bar(nut_df.sort_values('Amount', ascending=False).head(15), x='Amount', y='Nutrient',
                                 orientation='h', color='Amount')
                    st.plotly_chart(fig, use_container_width=True)
                with col_recipe:
                    rs.show_recipe_section(selected_food['description'])


    # --- 9. AI CHATBOT SECTION (PERMANENTLY VISIBLE) ---

    # --- 9. AI CHATBOT SECTION (AUTO-MODEL RECOVERY) ---

    from groq import Groq


    # --- 9. AI CHATBOT SECTION (POWERED BY GROQ) ---

    def handle_ai_chat():
        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.divider()
        st.subheader("👨‍⚕️ Expert Diabetes Consultation (Powered by Groq)")

        col_doc, col_intro = st.columns([1, 4])
        with col_doc:
            # Anh thay file ảnh bác sĩ của anh vào đây nhé
            st.image("https://cdn-icons-png.flaticon.com/512/387/387561.png", width=100)
        with col_intro:
            st.write("**Dr. AI Assistant**")
            st.caption("Specializing in Endocrinology & Nutrition")

        with st.container(border=True):
            # Hiển thị lịch sử chat
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Ô nhập liệu tiếng Anh
            if user_query := st.chat_input("Hello! I am your doctor. How can I help you?"):
                st.chat_message("user").markdown(user_query)
                st.session_state.messages.append({"role": "user", "content": user_query})

                with st.spinner("Doctor is responding instantly..."):
                    try:
                        # Khởi tạo Groq Client với Key anh cung cấp
                        # Tốt nhất anh nên đưa key này vào st.secrets["GROQ_API_KEY"]
                        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                        # Gọi model Llama 3 trên Groq
                        completion = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system",
                                 "content": "You are a professional diabetes doctor at the Institute of Environmental Technology. Answer scientifically and concisely in English."},
                                {"role": "user", "content": user_query}
                            ],
                            temperature=0.7,
                            max_tokens=1024,
                        )

                        ai_response = completion.choices[0].message.content

                        with st.chat_message("assistant"):
                            st.markdown(ai_response)
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})

                    except Exception as e:
                        st.error(f"Groq API Error: {str(e)}")


    # Gọi hàm ở cuối file
    handle_ai_chat()

    # --- TAB 2: ELITE FOODS LAB ---
    with tab_recommend:
        with st.expander(L["admin_title"]):
            with st.form("admin_form"):
                t = st.text_input("Title")
                c = st.selectbox("Category", ["Beans", "Nuts", "Seeds", "Greens"])
                img = st.text_input("Image URL")
                content = st.text_area("Content")
                if st.form_submit_button(L["publish_btn"]):
                    articles_col.insert_one(
                        {"title": t, "category": c, "image": img, "content": content, "date": datetime.now(),
                         "comments": []})
                    st.rerun()

        articles = list(articles_col.find().sort("date", -1))
        grid = st.columns(3)
        for idx, art in enumerate(articles):
            with grid[idx % 3]:
                st.image(art.get('image') or "https://via.placeholder.com/300", use_container_width=True)
                st.subheader(art['title'])
                if st.button(L["read_more"], key=f"art_{art['_id']}"):
                    st.session_state.selected_article_id = art['_id']

        if 'selected_article_id' in st.session_state:
            det = articles_col.find_one({"_id": st.session_state.selected_article_id})
            if det:
                st.markdown("---")
                st.header(det['title'])
                st.write(det['content'])
                st.subheader(L["discussion"])
                for cmt in det.get('comments', []):
                    with st.chat_message("user"): st.write(f"**{cmt['user']}**: {cmt['text']}")
                with st.form("cmt_form", clear_on_submit=True):
                    u = st.text_input(L["name_label"])
                    m = st.text_area(L["msg_label"])
                    if st.form_submit_button(L["comment_btn"]):
                        if not is_spam(m):
                            articles_col.update_one({"_id": det["_id"]}, {
                                "$push": {"comments": {"user": u or "Anon", "text": m, "time": datetime.now()}}})
                            st.rerun()

    # --- TAB 3: ABOUT ---
    with tab_about:
        st.info("System optimized for Environmental Toxicology and Nutritional Research. Researcher: Thao Thanh Nguyen")

    st.markdown(f"<div style='text-align:center; color:gray; margin-top:50px;'>{L['source']}</div>",
                unsafe_allow_html=True)