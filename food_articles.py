import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import time

# --- KẾT NỐI MONGODB ---
MONGO_URI = "mongodb+srv://nqtrung79_db_user:3fEes8fqxU67cTD4@foodata.yalh6q4.mongodb.net/?appName=Foodata"
client = MongoClient(MONGO_URI)
db = client['Foodata']
articles_col = db['food_articles']


# --- HÀM CHỐNG RÁC (ANTI-SPAM) ---
def is_spam(comment_text):
    bad_words = ['spam', 'quảng cáo', 'mua hàng', 'http', 'https', 'www']
    # 1. Kiểm tra từ khóa cấm
    if any(word in comment_text.lower() for word in bad_words):
        return True
    # 2. Kiểm tra độ dài (quá ngắn hoặc quá dài)
    if len(comment_text) < 5 or len(comment_text) > 500:
        return True
    return False


# --- GIAO DIỆN ADMIN (Dành cho anh Thanh đăng bài) ---
def admin_panel():
    with st.expander("🛠️ Admin: Đăng bài viết mới"):
        with st.form("add_article_form"):
            title = st.text_input("Tên thực phẩm (VD: Pinto Beans)")
            category = st.selectbox("Nhóm", ["Beans", "Nuts", "Seeds", "Greens", "Spices"])
            image_url = st.text_input("Link ảnh thực phẩm (URL)")
            content = st.text_area("Nội dung chi tiết bài viết")
            submitted = st.form_submit_button("Xuất bản bài viết")

            if submitted and title and content:
                article = {
                    "title": title,
                    "category": category,
                    "image": image_url,
                    "content": content,
                    "created_at": datetime.now(),
                    "comments": []
                }
                articles_col.insert_one(article)
                st.success(f"Đã đăng bài về {title}!")
                st.rerun()


# --- GIAO DIỆN HIỂN THỊ (Dành cho người dùng) ---
def elite_foods_lab():
    st.title("🛡️ Elite Foods Lab")
    st.markdown("---")

    # Mở quyền Admin nếu cần (Có thể thêm pass để bảo mật)
    admin_panel()

    # Lấy dữ liệu từ bài viết
    articles = list(articles_col.find().sort("created_at", -1))

    # Bố cục dạng Grid (lưới)
    cols = st.columns(3)
    for idx, doc in enumerate(articles):
        with cols[idx % 3]:
            st.image(doc.get('image', 'https://via.placeholder.com/150'), use_container_width=True)
            st.subheader(doc['title'])
            st.caption(f"Category: {doc['category']}")

            # Nút bấm mở chi tiết
            if st.button(f"Xem chi tiết {doc['title']}", key=f"btn_{doc['_id']}"):
                st.session_state.selected_article = doc['_id']

    # Giao diện bài viết chi tiết & Comment
    if 'selected_article' in st.session_state:
        st.markdown("---")
        selected_doc = articles_col.find_one({"_id": st.session_state.selected_article})

        if selected_doc:
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                st.image(selected_doc.get('image', ''), use_container_width=True)
            with col_txt:
                st.header(selected_doc['title'])
                st.write(selected_doc['content'])

            # --- PHẦN COMMENT ---
            st.subheader("💬 Thảo luận")

            # Hiển thị các comment cũ
            for cmt in selected_doc.get('comments', []):
                with st.chat_message("user"):
                    st.write(f"**{cmt['user']}**: {cmt['text']}")
                    st.caption(cmt['time'])

            # Form gửi comment mới
            with st.form("comment_form", clear_on_submit=True):
                user_name = st.text_input("Tên của bạn")
                comment_text = st.text_area("Ý kiến của bạn")
                submit_cmt = st.form_submit_button("Gửi bình luận")

                if submit_cmt:
                    # Chống gửi rác liên tục (Rate limit bằng session_state)
                    last_cmt_time = st.session_state.get('last_cmt_time', 0)
                    if time.time() - last_cmt_time < 60:  # Phải đợi 60s
                        st.warning("Bạn đang gửi quá nhanh! Vui lòng đợi 1 phút.")
                    elif is_spam(comment_text):
                        st.error("Bình luận chứa nội dung không phù hợp hoặc là rác!")
                    else:
                        new_comment = {
                            "user": user_name if user_name else "Ẩn danh",
                            "text": comment_text,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        articles_col.update_one(
                            {"_id": selected_doc['_id']},
                            {"$push": {"comments": new_comment}}
                        )
                        st.session_state.last_cmt_time = time.time()
                        st.success("Đã gửi bình luận!")
                        st.rerun()


if __name__ == "__main__":
    elite_foods_lab()