# WORLA – ENTERPRISE ACADEMIC SYSTEM
# Single-file | Streamlit | Desktop-ready

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="WORLA", layout="wide")

DB = "worla.db"

ROLES = ["Admin", "Instructor", "Student", "Parent"]

# Optional SMS (Twilio)
# USE_SMS = False
# TWILIO_SID = ""
# TWILIO_TOKEN = ""
# TWILIO_NUMBER = ""

# =========================
# DATABASE
# =========================
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT,
    linked_student TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS records (
    student TEXT,
    parent TEXT,
    course TEXT,
    year INTEGER,
    quarter TEXT,
    total INTEGER,
    grade TEXT,
    feedback TEXT,
    day TEXT,
    date TEXT
)
""")
conn.commit()

# =========================
# HELPERS
# =========================
def grade(score):
    if score >= 180: return "A"
    if score >= 160: return "B"
    if score >= 140: return "C"
    if score >= 120: return "D"
    return "F"

def generate_pdf(student, df):
    file = f"{student}_report.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"Report Card: {student}", styles["Title"])]

    for _, r in df.iterrows():
        story.append(
            Paragraph(
                f"{r['course']} {r['year']} {r['quarter']} "
                f"→ {r['total']} ({r['grade']})",
                styles["Normal"]
            )
        )

    doc.build(story)
    return file

# =========================
# AUTH
# =========================
st.title("🎓 Academic Record Academic System")

role = st.selectbox("Role", ROLES, key="login_role")
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=? AND role=?",
        (username, password, role)
    )
    if c.fetchone():
        st.session_state.user = (username, role)
    else:
        st.error("Invalid credentials")

if "user" not in st.session_state:
    st.stop()

user, role = st.session_state.user

# =========================
# ADMIN
# =========================
if role == "Admin":
    st.sidebar.header("Admin Panel")

    if st.sidebar.button("Create User"):
        u = st.text_input("kella")
        p = st.text_input("Passcode", type="password")
        r = st.selectbox("Role", ROLES, key="create_user_role")
        s = st.text_input("Linked Student (for Parent)")
        if st.button("Save User"):
            c.execute(
                "INSERT OR IGNORE INTO users VALUES (?,?,?,?)",
                (u, p, r, s)
            )
            conn.commit()
            st.success("User created")

    if st.sidebar.button("Delete User"):
        st.sidebar.write("Delete existing user")
        del_user = st.sidebar.text_input("Username to delete")
        if st.sidebar.button("Confirm Delete User"):
            c.execute("DELETE FROM users WHERE username=?", (del_user,))
            conn.commit()
            st.sidebar.success(f"User '{del_user}' deleted")

    st.subheader("👥 All Users")
    users_df = pd.read_sql("SELECT username, role, linked_student FROM users", conn)
    st.dataframe(users_df)

    st.subheader("📚 All Student Records")
    records_df = pd.read_sql("SELECT * FROM records", conn)
    st.dataframe(records_df)

# =========================
# INSTRUCTOR
# =========================
if role == "Instructor":
    st.sidebar.header("Instructor")

    student = st.text_input("Student Name")
    parent = st.text_input("Parent Name")
    course = st.text_input("Course")
    year = st.number_input("Year", 2020, 2100, datetime.now().year)
    quarter = st.selectbox("Quarter", ["Q1","Q2","Q3","Q4"])
    total = st.number_input("Total Score", 0, 200)

    if st.button("Save Record"):
        today = datetime.now()
        g = grade(total)

        c.execute("""
        INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            student, parent, course, year, quarter,
            total, g, "Auto feedback",
            today.strftime("%A"), today.strftime("%Y-%m-%d")
        ))
        conn.commit()
        st.success("Record saved")

    st.sidebar.write("---")
    st.subheader("📊 All Student Records")
    all_records = pd.read_sql("SELECT * FROM records", conn)
    st.dataframe(all_records)

    if st.sidebar.button("Delete Record"):
        st.sidebar.write("Delete a student record")
        del_student = st.sidebar.text_input("Student name to delete from")
        del_course = st.sidebar.text_input("Course name to delete")
        if st.sidebar.button("Confirm Delete Record"):
            c.execute("DELETE FROM records WHERE student=? AND course=?", (del_student, del_course))
            conn.commit()
            st.sidebar.success(f"Record deleted for {del_student} - {del_course}")

# =========================
# STUDENT
# =========================
if role == "Student":
    st.header("Student Portal")
    df = pd.read_sql(
        "SELECT * FROM records WHERE student=?",
        conn, params=(user,)
    )
    st.dataframe(df)

    if not df.empty:
        pdf = generate_pdf(user, df)
        st.download_button("Download PDF", open(pdf,"rb"), pdf)

    if st.button("Delete My Record"):
        del_course = st.text_input("Course to delete")
        if st.button("Confirm Delete"):
            c.execute("DELETE FROM records WHERE student=? AND course=?", (user, del_course))
            conn.commit()
            st.success(f"Record deleted for {del_course}")
            st.rerun()

# =========================
# PARENT
# =========================
if role == "Parent":
    st.header("Parent Portal")
    c.execute(
        "SELECT linked_student FROM users WHERE username=?",
        (user,)
    )
    student = c.fetchone()[0]

    df = pd.read_sql(
        "SELECT * FROM records WHERE student=?",
        conn, params=(student,)
    )
    st.dataframe(df)

    if not df.empty:
        pdf = generate_pdf(student, df)
        st.download_button("Download Child Report", open(pdf,"rb"), pdf)

    if st.button("Delete Child Record"):
        del_course = st.text_input("Course record to delete")
        if st.button("Confirm Delete Child Record"):
            c.execute("DELETE FROM records WHERE student=? AND course=?", (student, del_course))
            conn.commit()
            st.success(f"Record deleted for {student} - {del_course}")
            st.rerun()
