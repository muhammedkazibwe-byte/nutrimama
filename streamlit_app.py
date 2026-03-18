import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

conn = sqlite3.connect("nutrimama.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS food_logs 
             (id INTEGER PRIMARY KEY, mother TEXT, date TEXT, score INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS orders 
             (id INTEGER PRIMARY KEY, mother TEXT, items TEXT, status TEXT)''')
conn.commit()

if "role" not in st.session_state:
    st.session_state.role = None
if "current_screen" not in st.session_state:
    st.session_state.current_screen = "login"

st.set_page_config(page_title="NutriMama", page_icon="🌿")
st.title("🌿 NutriMama")
st.caption("Full-Stack App for STI-OP Pitch")

if st.session_state.current_screen == "login":
    st.subheader("Phone Login")
    phone = st.text_input("Phone number", "+256700000000")
    if st.button("Send OTP"): st.success("OTP sent (demo)")
    otp = st.text_input("Enter OTP", "123456")
    if st.button("Verify OTP"):
        st.session_state.current_screen = "language"
        st.rerun()

elif st.session_state.current_screen == "language":
    st.subheader("Select Language")
    lang = st.selectbox("Language", ["English", "Luganda", "Swahili", "Runyankole"])
    if st.button("Continue"):
        st.session_state.current_screen = "role"
        st.rerun()

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

else:
    role = st.session_state.role
    st.sidebar.success(f"Logged in as {role}")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if role == "Mother":
        st.header("👩‍🍼 Welcome back, Amina")
        col1, col2 = st.columns(2)
        with col1: st.metric("Subscription", "Monthly Active", "✅")
        with col2: st.metric("Current MDD-W", "7/10", "✅")
        st.line_chart(pd.DataFrame({"Day": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], "Score": [4,5,6,7,8,7,9]}).set_index("Day"))
        if st.button("➕ Log Today's Food", type="primary", use_container_width=True):
            st.session_state.current_screen = "food_log"
            st.rerun()

    elif st.session_state.current_screen == "food_log":
        st.subheader("Daily Food Logging")
        groups = ["Grains", "Pulses", "Dark green veg", "Vitamin A veg", "Other veg", "Fruits", "Meat/Fish", "Eggs", "Dairy"]
        selected = st.multiselect("Select foods eaten", groups)
        if st.button("Submit & Get AI Advice", type="primary"):
            score = len(selected)
            c.execute("INSERT INTO food_logs (mother, date, score) VALUES (?,?,?)", ("Amina", str(date.today()), score))
            conn.commit()
            st.success(f"MDD-W Score: {score}/10")
            if score < 5:
                st.error("🤖 AI Advice: Add more dark green vegetables and pulses")
            if st.button("Back"):
                st.session_state.current_screen = "dashboard"
                st.rerun()

st.caption("NutriMama Full Stack • KIU Western Campus")
