import streamlit as st


def get_smart_recipe(food_name):
    # Dictionary chứa công thức cho các nhóm thực phẩm chính
    # Bạn có thể mở rộng danh sách này lên hàng trăm món dễ dàng
    recipe_db = {
        "tomato": {
            "title": "Fresh Tomato & Basil Salad",
            "img": "https://images.unsplash.com/photo-1592417817098-8fd3d9ebc4a5?q=80&w=300",
            "steps": ["Slice tomatoes", "Add fresh basil", "Drizzle with olive oil", "No salt added"],
            "url": "https://www.diabetesfoodhub.org/recipes/tomato-basil-salad.html"
        },
        "oats": {
            "title": "Overnight Oats with Berries",
            "img": "https://images.unsplash.com/photo-1517673132405-a56a62b18caf?q=80&w=300",
            "steps": ["Mix oats with unsweetened almond milk", "Add chia seeds", "Top with blueberries",
                      "Rest overnight"],
            "url": "https://www.diabetesfoodhub.org/recipes/overnight-berry-oats.html"
        },
        "chicken": {
            "title": "Lemon Herb Grilled Chicken",
            "img": "https://images.unsplash.com/photo-1532550907401-a500c9a57435?q=80&w=300",
            "steps": ["Marinate with lemon & garlic", "Grill until golden", "Serve with steamed broccoli"],
            "url": "https://www.diabetesfoodhub.org/recipes/lemon-herb-grilled-chicken.html"
        }
    }

    # Tìm kiếm công thức dựa trên từ khóa trong tên thực phẩm
    name_lower = food_name.lower()
    for key in recipe_db:
        if key in name_lower:
            return recipe_db[key]
    return None


def show_recipe_section(food_name):
    st.subheader("👨‍🍳 Diabetic-Friendly Recipe")

    recipe = get_smart_recipe(food_name)

    if recipe:
        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.image(recipe['img'], use_container_width=True)
        with col2:
            st.markdown(f"### {recipe['title']}")
            st.write("**Quick Steps:**")
            for step in recipe['steps']:
                st.write(f"- {step}")
            st.link_button("View Full Details", recipe['url'])
    else:
        # Nếu không có trong DB, gợi ý tìm kiếm nhanh trên Diabetes Food Hub
        clean_name = food_name.split(',')[0]
        st.info(f"Searching custom recipes for {clean_name}...")
        search_url = f"https://www.diabetesfoodhub.org/search-results.html?keywords={clean_name.replace(' ', '%20')}"
        st.link_button(f"🔍 Find {clean_name} Recipes on Food Hub", search_url)

    st.markdown("---")
    st.caption("Recommended Cooking Tutorial")
    st.video("https://www.youtube.com/watch?v=X9ivR4y03DE")