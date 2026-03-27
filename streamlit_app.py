import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
from groq import Groq

st.set_page_config(page_title="NutriMama", page_icon="👩‍🍼", layout="centered")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq = Groq(api_key=GROQ_API_KEY)

MDDW_GROUPS = [
    "Starchy Staples (Matooke, Rice, Cassava, Potatoes)",
    "Pulses (Beans, Cowpeas, Lentils)",
    "Nuts & Seeds (G-nuts, Simsim)",
    "Dairy (Milk, Yoghurt)",
    "Meat, Poultry & Fish",
    "Eggs",
    "Dark Green Leafy Vegetables (Dodo, Sukuma Wiki, Spinach)",
    "Vitamin A Rich Fruits & Vegetables (Mangoes, Pumpkins, Carrots)",
    "Other Fruits",
    "Other Vegetables (Cabbage, Tomatoes, Onions)"
]

# ================== SESSION STATE ==================
if "page" not in st.session_state: st.session_state.page = "language"
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None
if "accepted_job" not in st.session_state: st.session_state.accepted_job = None

# ================== LANGUAGE & LOGIN ==================
if st.session_state.page == "language":
    st.title("🌍 NutriMama")
    if st.button("Continue → English", type="primary"):
        st.session_state.page = "demo_login"
        st.rerun()

elif st.session_state.page == "demo_login":
    st.title("👋 Welcome to NutriMama")
    phone = st.text_input("Phone number", "+25683117299")
    if st.button("Send Demo OTP", type="primary"):
        st.success("✅ Demo OTP sent! Code is **123456**")
        st.session_state.temp_phone = phone
        st.rerun()
    if "temp_phone" in st.session_state:
        code = st.text_input("Enter OTP", max_chars=6)
        if st.button("Verify"):
            if code == "123456":
                st.session_state.user = {"phone": st.session_state.temp_phone}
                st.session_state.page = "profile_setup"
                st.success("✅ Logged in!")
                st.rerun()

# ================== PROFILE SETUP (ALL ROLES) ==================
elif st.session_state.page == "profile_setup":
    st.title("👤 Complete Your Profile")
    name = st.text_input("Full Name", "Amina Nakato")
    role_choice = st.selectbox("Your Role", ["Mother", "Vendor", "Bodaboda Rider", "CHW"])
    
    extra = {}
    if role_choice == "Mother":
        age = st.number_input("Age", 18, 45, 28)
        trimester = st.selectbox("Trimester", ["1st", "2nd", "3rd"])
        extra = {"age": age, "trimester": trimester}
    
    if st.button("Save Profile & Continue", type="primary"):
        supabase.table("profiles").upsert({
            "phone": st.session_state.user["phone"],
            "name": name,
            "role": role_choice,
            **extra
        }).execute()
        st.session_state.user["name"] = name
        st.session_state.role = role_choice
        st.session_state.page = "dashboard"
        st.success("✅ Profile saved!")
        st.rerun()

elif st.session_state.page == "dashboard":
    role = st.session_state.role
    st.title(f"{role} Dashboard — {st.session_state.user.get('name', '')}")

    if role == "Mother":
        st.subheader("📦 Choose Your Plan & Basket")
        plan = st.radio("What do you want?", ["AI Advice only (FREE)", "Delivery only", "Both AI Advice + Delivery"], horizontal=True)
        
        if plan in ["Delivery only", "Both AI Advice + Delivery"]:
            basket_option = st.radio("Basket size", ["Basket 1 (exactly 5 foods) - 50,000 UGX/week", "Basket 2 (exactly 7 foods) - 70,000 UGX/week", "Basket 3 (exactly 10 foods) - 80,000 UGX/week"], horizontal=True)
            max_foods = 5 if "5" in basket_option else 7 if "7" in basket_option else 10
            selected_foods = st.multiselect(f"Choose exactly {max_foods} foods", MDDW_GROUPS)
            
            if st.button("Subscribe & Save", type="primary"):
                if len(selected_foods) != max_foods:
                    st.error(f"❌ Select exactly {max_foods} foods!")
                else:
                    supabase.table("orders").insert({
                        "phone": st.session_state.user["phone"],
                        "mother_name": st.session_state.user["name"],
                        "basket_size": basket_option,
                        "selected_foods": selected_foods,
                        "price": 50000 if max_foods==5 else 70000 if max_foods==7 else 80000,
                        "status": "New"
                    }).execute()
                    st.success(f"✅ {plan} subscribed!")
                    st.balloons()

        # AI Food Log only for AI Advice or Both
        if plan != "Delivery only":
            st.subheader("🍲 Daily Food Log + Smart AI Coach")
            selected = st.multiselect("Foods you ate yesterday", MDDW_GROUPS)
            if st.button("Save Log → Get AI Assessment"):
                score = len(selected)
                supabase.table("food_logs").insert({
                    "phone": st.session_state.user["phone"],
                    "date": datetime.now().isoformat(),
                    "groups": selected,
                    "mddw_score": score
                }).execute()
                # AI call
                prompt = f"You are NutriMama's caring AI coach. Mother {st.session_state.user.get('name')} ate {score}/10 groups. Give one motivator and one reminder."
                try:
                    resp = groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=150)
                    ai_message = resp.choices[0].message.content.strip()
                except:
                    ai_message = "You're doing great for your baby! Reminder: Eat before 8pm tomorrow."
                st.info(f"**AI Coach says:** {ai_message}")

    elif role == "Vendor":
        st.subheader("📦 Live Orders")
        response = supabase.table("orders").select("*").execute()
        if response.data:
            for order in response.data:
                col1, col2 = st.columns([4, 1])
                with col1:
                    foods = ", ".join(order.get("selected_foods", []))
                    st.write(f"**{order['mother_name']}** — {order['basket_size']}")
                    st.caption(foods)
                with col2:
                    if st.button("Mark Ready", key=f"ready_{order.get('id')}"):
                        supabase.table("orders").update({"status": "Ready"}).eq("id", order["id"]).execute()
                        st.success("✅ Marked Ready!")
                        st.rerun()
        else:
            st.info("No orders yet")

    elif role == "Rider" or role == "Bodaboda Rider":
        st.subheader("🚀 Available Delivery Jobs")
        response = supabase.table("orders").select("*").eq("status", "New").execute()
        if response.data:
            for order in response.data:
                if st.button(f"Accept delivery for {order['mother_name']} — {order['basket_size']}", key=f"accept_{order.get('id')}"):
                    st.session_state.accepted_job = order
                    st.success("✅ Accepted! Map loading...")
                    st.rerun()
        else:
            st.info("No pending jobs yet")

        if st.session_state.accepted_job is not None:
            job = st.session_state.accepted_job
            st.subheader(f"🗺️ Navigation — {job['mother_name']}")
            st.write(f"**Pickup:** Vendor Shop - Makerere")
            st.write(f"**Delivering to:** {job['mother_name']}")
            map_data = pd.DataFrame({
                "lat": [0.3476, 0.3550, 0.3135],
                "lon": [32.5825, 32.5900, 32.5741],
                "name": ["You (Rider)", job["mother_name"], "Pickup Point"]
            })
            st.map(map_data, use_container_width=True, zoom=13)
            if st.button("Mark Delivered"):
                uploaded = st.file_uploader("Upload proof photo", type=["jpg","png"])
                if uploaded:
                    st.image(uploaded, width=400)
                    st.success("✅ Delivered!")
                    st.session_state.accepted_job = None
                    st.rerun()

    elif role == "CHW":
        st.subheader("⚠️ Active Alerts")
        alerts = supabase.table("alerts").select("*").eq("seen", False).execute()
        if alerts.data:
            for alert in alerts.data:
                st.write(f"**{alert['mother_name']}** — {alert['alert_type']}")
                st.caption(alert['message'])
            if st.button("Mark All Seen"):
                supabase.table("alerts").update({"seen": True}).eq("seen", False).execute()
                st.success("✅ All alerts marked as seen")
        else:
            st.success("No active alerts")

    if st.button("Logout"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

st.caption("NutriMama — Real Sign-up for ALL roles + Delivery-only fix + Live Rider Map")
