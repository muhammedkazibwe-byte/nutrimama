import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
from groq import Groq

st.set_page_config(page_title="NutriMama", page_icon="👩‍🍼", layout="centered")

# --- SECRETS & CLIENTS ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq = Groq(api_key=GROQ_API_KEY)

MDDW_GROUPS = [
    "Grains, white roots & tubers (matooke, rice)",
    "Pulses (beans, peas, lentils)",
    "Nuts & seeds",
    "Dairy (milk, yoghurt)",
    "Meat, poultry & fish",
    "Eggs",
    "Dark green leafy vegetables (sukuma wiki)",
    "Vitamin A rich fruits & vegetables",
    "Other fruits",
    "Other vegetables"
]

if "page" not in st.session_state: st.session_state.page = "language"
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None
if "active_job_id" not in st.session_state: st.session_state.active_job_id = None

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
    if "temp_phone" in st.session_state:
        code = st.text_input("Enter OTP", max_chars=6)
        if st.button("Verify"):
            if code == "123456":
                st.session_state.user = {"phone": st.session_state.temp_phone}
                st.session_state.page = "profile_setup"
                st.rerun()

elif st.session_state.page == "profile_setup":
    st.title("👤 Complete Your Profile")
    name = st.text_input("Full Name", "Amina Nakato")
    role_choice = st.selectbox("Your Role", ["Mother", "Vendor", "Bodaboda Rider", "CHW"])
    extra = {}
    if role_choice == "Mother":
        age = st.number_input("Age", 18, 45, 28)
        trimester = st.selectbox("Trimester", ["1st", "2nd", "3rd"])
        extra = {"age": age, "trimester": trimester}
    if st.button("Save Profile & Continue"):
        supabase.table("profiles").upsert({"phone": st.session_state.user["phone"], "name": name, "role": role_choice, **extra}).execute()
        st.session_state.user["name"] = name
        st.session_state.role = role_choice
        st.session_state.page = "dashboard"
        st.rerun()

elif st.session_state.page == "dashboard":
    role = st.session_state.role
    st.title(f"{role} Dashboard")
    if role == "Mother":
        st.subheader("📦 Subscription & Delivery")
        plan = st.radio("Select Service", ["AI Advice only (FREE)", "Delivery only", "Both AI Advice + Delivery"], horizontal=True)
        if plan in ["Delivery only", "Both AI Advice + Delivery"]:
            basket = st.selectbox("Choose Basket", ["Basket 1 (5 items)", "Basket 2 (7 items)", "Basket 3 (10 items)"])
            max_f = 5 if "5" in basket else 7 if "7" in basket else 10
            selected = st.multiselect(f"Pick {max_f} items", MDDW_GROUPS)
            if st.button("Place Order") and len(selected) == max_f:
                supabase.table("orders").insert({"phone": st.session_state.user["phone"], "mother_name": st.session_state.user["name"], "basket_size": basket, "selected_foods": selected, "status": "New"}).execute()
                st.success("Order Placed!")
        if plan in ["AI Advice only (FREE)", "Both AI Advice + Delivery"]:
            st.divider()
            st.subheader("🍲 Daily Food Log + AI Coach")
            ate = st.multiselect("What did you eat yesterday?", MDDW_GROUPS)
            if st.button("Get AI Feedback"): st.info("AI Coach: Analyzing diversity...")

    elif role == "Bodaboda Rider":
        if st.session_state.active_job_id is None:
            st.subheader("🚀 Available Jobs")
            jobs = supabase.table("orders").select("*").eq("status", "New").execute()
            for job in jobs.data:
                if st.button(f"Accept: {job['mother_name']}", key=job['id']):
                    supabase.table("orders").update({"status": "Picked Up"}).eq("id", job['id']).execute()
                    st.session_state.active_job_id = job['id']
                    st.rerun()
        else:
            st.subheader("🗺️ Active Navigation")
            if st.button("Complete Delivery"):
                supabase.table("orders").update({"status": "Delivered"}).eq("id", st.session_state.active_job_id).execute()
                st.session_state.active_job_id = None
                st.rerun()

    elif role == "Vendor":
        st.subheader("🏪 Kitchen Orders")
        orders = supabase.table("orders").select("*").eq("status", "New").execute()
        for o in orders.data:
            if st.button(f"Ready: {o['mother_name']}", key=o['id']):
                supabase.table("orders").update({"status": "Ready"}).eq("id", o['id']).execute()
                st.rerun()

    elif role == "CHW":
        st.subheader("⚠️ Health Alerts")
        alerts = supabase.table("alerts").select("*").eq("seen", False).execute()
        for a in alerts.data: st.error(f"ALERT: {a['mother_name']} - {a['message']}")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
