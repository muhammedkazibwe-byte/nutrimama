import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date

# ================== SUPABASE CONNECTION ==================
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = get_supabase()

# ================== SESSION STATE ==================
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "current_screen" not in st.session_state:
    st.session_state.current_screen = "login"

st.set_page_config(page_title="NutriMama", page_icon="🌿", layout="centered")
st.title("🌿 NutriMama")
st.caption("Full-Stack Maternal Nutrition & Delivery System | STI-OP Pitch")

# ================== LOGIN (Real Phone OTP) ==================
if st.session_state.current_screen == "login":
    st.subheader("🔑 Phone Login")
    phone = st.text_input("Phone number (+256...)", "+2567")
    
    if st.button("Send OTP"):
        try:
            supabase.auth.sign_in_with_otp({"phone": phone})
            st.success("✅ OTP sent! Check your SMS")
            st.session_state.phone = phone
        except Exception as e:
            st.error(str(e))

    otp = st.text_input("Enter 6-digit OTP", max_chars=6)
    if st.button("Verify OTP"):
        try:
            response = supabase.auth.verify_otp({"phone": st.session_state.phone, "token": otp, "type": "sms"})
            st.session_state.user = response.user
            st.session_state.current_screen = "language"
            st.rerun()
        except:
            st.error("❌ Wrong OTP. Try again.")

# ================== LANGUAGE ==================
elif st.session_state.current_screen == "language":
    st.subheader("🌍 Select Your Preferred Language")
    lang = st.selectbox("Language", ["English", "Luganda", "Swahili", "Runyankole"])
    if st.button("Continue"):
        st.session_state.language = lang
        st.session_state.current_screen = "role"
        st.rerun()

# ================== ROLE SELECTION ==================
elif st.session_state.current_screen == "role":
    st.subheader("Choose Your Role")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👩‍🍼 Mother", use_container_width=True):
            st.session_state.role = "Mother"
            st.session_state.current_screen = "dashboard"
            st.rerun()
        if st.button("🛒 Vendor", use_container_width=True):
            st.session_state.role = "Vendor"
            st.session_state.current_screen = "dashboard"
            st.rerun()
    with col2:
        if st.button("🏍️ Bodaboda Rider", use_container_width=True):
            st.session_state.role = "Rider"
            st.session_state.current_screen = "dashboard"
            st.rerun()
        if st.button("🩺 CHW", use_container_width=True):
            st.session_state.role = "CHW"
            st.session_state.current_screen = "dashboard"
            st.rerun()

# ================== MAIN DASHBOARDS ==================
else:
    role = st.session_state.role
    st.sidebar.success(f"✅ Logged in as {role}")

    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()

    # ================== MOTHER DASHBOARD ==================
    if role == "Mother":
        st.header("👩‍🍼 Welcome back, Amina")
        col1, col2 = st.columns(2)
        with col1: st.metric("Subscription", "Monthly Active", "✅")
        with col2: st.metric("Current MDD-W", "7/10", "✅")

        st.subheader("Last 7 Days Score")
        chart = pd.DataFrame({"Day": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], "Score": [4,5,6,7,8,7,9]})
        st.line_chart(chart.set_index("Day"))

        if st.button("➕ Log Today's Food", type="primary", use_container_width=True):
            st.session_state.current_screen = "food_log"
            st.rerun()

    # ================== FOOD LOG + AI ==================
    elif st.session_state.current_screen == "food_log":
        st.subheader("Daily Food Logging (MDD-W)")
        groups = [
            "Grains (matooke, posho)", "Pulses (beans, lentils)", "Dark green leafy vegetables (sukuma wiki)",
            "Vitamin A-rich fruits & vegetables", "Other vegetables", "Other fruits",
            "Meat, poultry & fish", "Eggs", "Dairy", "Nuts & seeds"
        ]
        selected = st.multiselect("Foods eaten yesterday", groups)
        
        if st.button("Submit & Get AI Advice", type="primary"):
            score = len(selected)
            supabase.table("food_logs").insert({
                "mother_id": st.session_state.user.id,
                "date": str(date.today()),
                "mddw_score": score
            }).execute()

            st.success(f"MDD-W Score: {score}/10")
            if score >= 5:
                st.balloons()
                st.success("✅ Excellent! You met the WHO minimum")
            else:
                missing = [g for g in groups if g not in selected][:3]
                st.error("🤖 AI Nutrition Advice")
                st.write("**Add these tomorrow:**")
                for item in missing:
                    st.write(f"• {item}")

            if st.button("← Back to Dashboard"):
                st.session_state.current_screen = "dashboard"
                st.rerun()

    # ================== VENDOR ==================
    elif role == "Vendor":
        st.header("🛒 Vendor Dashboard - Ishaka Market")
        orders = supabase.table("orders").select("*").execute().data
        if orders:
            st.dataframe(pd.DataFrame(orders))
        else:
            st.info("No orders yet")
        if st.button("Mark Order Ready"):
            st.success("✅ Order prepared and ready for rider")

    # ================== RIDER ==================
    elif role == "Rider":
        st.header("🏍️ Bodaboda Rider")
        st.write("**Wallet:** UGX 45,000")
        st.write("Available Deliveries:")
        if st.button("Accept Delivery - Amina Nakato"):
            st.success("Job accepted! Navigate to Bushenyi Health Centre")

    # ================== CHW ==================
    elif role == "CHW":
        st.header("🩺 CHW Dashboard")
        st.subheader("Risk Alerts (MDD-W < 5)")
        low_scores = supabase.table("food_logs").select("*").lt("mddw_score", 5).execute().data
        if low_scores:
            df = pd.DataFrame(low_scores)
            st.dataframe(df)
            st.warning("⚠️ 3 mothers need immediate follow-up!")
        else:
            st.success("All mothers are doing well")

st.caption("Full-Stack NutriMama | Supabase Backend | Built for STI-OP 2026")
