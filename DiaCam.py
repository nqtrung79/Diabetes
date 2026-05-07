import streamlit as st
from google import genai
from PIL import Image
import pandas as pd
from pymongo import MongoClient
import io
import time
from groq import Groq


# --- CÁC HÀM XỬ LÝ LOGIC ---

def get_available_gemini_model(client_gemini):
    try:
        models = [m.name for m in client_gemini.models.list() if 'generateContent' in m.supported_methods]
        for m in ["models/gemini-2.0-flash", "models/gemini-2.5-flash"]:
            if m in models: return m
        return models[0]
    except:
        return "gemini-2.5-flash"


def lookup_and_calculate(db, keyword):
    """Tìm kiếm trực tiếp trên Scored_Foods và Join với Core_Nutrients"""
    words = keyword.split()
    search_conditions = [{"description": {"$regex": word, "$options": "i"}} for word in words]

    scored_items = list(db.Scored_Foods.find({"$or": search_conditions}).limit(50))

    if not scored_items:
        return None

    cal_list = []
    gl_list = []

    for item in scored_items:
        fid = item.get('fdc_id')
        carb = item.get('Carbohydrate, by difference', 0)

        energy_data = db.Core_Nutrients.find_one({
            "fdc_id": int(fid),
            "nutrient_id": {"$in": [1008, 2047, 957]}
        })

        cal = energy_data.get('amount', 0) if energy_data else 0

        try:
            v_cal = float(cal)
            v_carb = float(carb)
            v_gl = (v_carb * 55) / 100

            if v_cal > 0 or v_carb > 0:
                cal_list.append(v_cal)
                gl_list.append(v_gl)
        except:
            continue

    if not cal_list and not gl_list:
        return None

    return {
        "keyword": keyword,
        "count": len(cal_list),
        "min_cal": min(cal_list) if cal_list else 0,
        "max_cal": max(cal_list) if cal_list else 0,
        "avg_cal": sum(cal_list) / len(cal_list) if cal_list else 0,
        "avg_gl": sum(gl_list) / len(gl_list) if gl_list else 0
    }


def analyze_with_groq(client_groq, ai_analysis, summary_data):
    prompt = f"""
    Bạn là chuyên gia dinh dưỡng. Hãy phân tích báo cáo sau:
    1. Nhận diện hình ảnh: {ai_analysis}
    2. Thống kê từ Database (50 mẫu/loại): 
    {summary_data}

    Yêu cầu:
    - Nhận xét về lượng Calo (Min/Max/Avg).
    - Đánh giá chỉ số GL trung bình của món ăn này đối với người tiểu đường.
    - Đưa ra lời khuyên cụ thể bằng tiếng Việt, ngắn gọn.
    """

    completion = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content


# --- HÀM CHÍNH ĐỂ APP.PY GỌI ---

def run_diacam_lab():
    st.subheader("📸 Food Intelligence: Calorie & GL Check")

    # --- THÊM LẠI ĐOẠN NÀY NẾU ANH MUỐN ---
    try:
        df_dict = pd.read_csv("usda_food_dictionary_clean.csv")
        st.success(f"📚 AI-Powered Glycemic Load Analysis** integrated with **{len(df_dict)}** USDA-standard food items for diabetic-safe decisions.")
    except:
        st.warning("⚠️ Không tìm thấy file usda_food_dictionary_clean.csv")
    # --------------------------------------
    # 1. CẤU HÌNH KẾT NỐI (Lấy từ st.secrets của app.py)
    try:
        client_gemini = genai.Client(
            api_key=st.secrets["GEMINI_API_KEY"],
            http_options={'api_version': 'v1'}
        )
        client_groq = Groq(api_key=st.secrets["Groq_API_KEY"])
        client_db = MongoClient(st.secrets["MONGO_URI"])
        db = client_db["USDA_Healthy_Food"]
    except Exception as e:
        st.error(f"Lỗi cấu hình: {e}")
        return

    # 2. GIAO DIỆN NHẬP ẢNH
    input_method = st.radio("Choose the way you upload your meal picture:", ["📤 Upload a picture", "📸 Take a picture"], horizontal=True)

    img_file = None
    if input_method == "📤 Upload a picture":
        img_file = st.file_uploader("Upload your picture here", type=['jpg', 'png', 'jpeg'])
    else:
        img_file = st.camera_input("Put your meal in the center")

    if img_file:
        img = Image.open(img_file)
        st.image(img, width=400, caption="Picture is saving")

        if st.button("🚀 Analyzing your meal"):
            full_text = ""
            with st.spinner("Step 1: Detect your meal..."):
                gemini_prompt = """
                Bạn là một chuyên gia dinh dưỡng. Hãy nhìn ảnh món ăn này và thực hiện:
                1. Phân tích các thành phần chính (Ví dụ: Phở bò có: Bánh phở, Thịt bò, Nước dùng).
                2. Với mỗi thành phần, hãy đưa ra 1 từ khóa cốt lõi nhất bằng tiếng Anh để tra cứu USDA.
                Trả về đúng cấu trúc:
                Analysis: [Phân tích tiếng Việt]
                Keywords: [key 1], [key 2]
                """
                model_name = get_available_gemini_model(client_gemini)
                res = client_gemini.models.generate_content(model=model_name, contents=[gemini_prompt, img])
                full_text = res.text
                st.write("✅ Completed.")

            if full_text:
                keywords = []
                analysis_part = ""
                for line in full_text.split('\n'):
                    if "Keywords:" in line:
                        keywords = [k.strip() for k in line.replace("Keywords:", "").split(',')]
                    if "Analysis:" in line:
                        analysis_part = line.replace("Analysis:", "")

                with st.spinner("Step 2: Checking Calories and GL..."):
                    summary_for_groq = ""
                    st.subheader("📊 Results from your meal")

                    for kw in keywords:
                        stats = lookup_and_calculate(db, kw)
                        if stats:
                            info = f"- {kw}: Calo ({stats['min_cal']:.0f}-{stats['max_cal']:.0f}), TB: {stats['avg_cal']:.1f}; GL TB: {stats['avg_gl']:.1f}"
                            summary_for_groq += info + "\n"

                            with st.expander(f"Detail for: {kw}"):
                                st.write(f"Detected **{stats['count']}** .")
                                st.write(
                                    f"🔥 Calories: minimum **{stats['min_cal']:.0f}** | maximum **{stats['max_cal']:.0f}** | average **{stats['avg_cal']:.1f}**")
                                st.write(f"🩸 Average GL index: **{stats['avg_gl']:.1f}**")
                        else:
                            st.warning(f"Không tìm thấy dữ liệu cho: {kw}")

                if summary_for_groq:
                    with st.spinner("Step 3: Advice from doctor..."):
                        final_report = analyze_with_groq(client_groq, analysis_part, summary_for_groq)
                        st.divider()
                        st.subheader("📝 Conclusion")
                        st.info(final_report)