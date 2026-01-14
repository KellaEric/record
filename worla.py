# worla.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="WORLA – Student Assessment System",
    layout="wide"
)

DATABASE = "worla_assessment.db"
INSTRUCTOR_PASSWORD = "instructor123"

# =========================
# DATABASE SETUP
# =========================
conn = sqlite3.connect(DATABASE, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS assessments (
    student TEXT,
    quarter TEXT,
    assignment INTEGER,
    project INTEGER,
    attendance INTEGER,
    quiz INTEGER,
    final_project INTEGER,
    research INTEGER,
    total INTEGER,
    grade TEXT,
    feedback TEXT,
    timestamp TEXT
)
""")
conn.commit()

# =========================
# HELPER FUNCTIONS
# =========================
def calculate_grade(score):
    if score >= 180:
        return "A"
    elif score >= 160:
        return "B"
    elif score >= 140:
        return "C"
    elif score >= 120:
        return "D"
    return "F"

def generate_feedback(score):
    if score >= 180:
        return "Outstanding performance. Excellent mastery of Python programming."
    elif score >= 160:
        return "Very good work. Improve code optimization and structure."
    elif score >= 140:
        return "Good effort. Practice algorithms and logic building."
    elif score >= 120:
        return "Fair performance. Needs more hands-on coding practice."
    else:
        return "Poor performance. Requires significant improvement and mentorship."

def add_student(name):
    c.execute("INSERT OR IGNORE INTO students (name) VALUES (?)", (name,))
    conn.commit()

def get_students():
    return [r[0] for r in c.execute("SELECT name FROM students")]

def save_assessment(data):
    c.execute("""
    INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, data)
    conn.commit()

def load_assessments():
    return pd.read_sql("SELECT * FROM assessments", conn)

# =========================
# AUTHENTICATION
# =========================
st.title("🎓 WORLA – Student Assessment System")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("Instructor Password", type="password")
    if st.button("Login"):
        if pwd == INSTRUCTOR_PASSWORD:
            st.session_state.auth = True
            st.success("Access granted")
        else:
            st.error("Invalid password")
    st.stop()

# =========================
# SIDEBAR MENU
# =========================
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Add Student",
        "Enter Assessment",
        "View Records",
        "Analytics Dashboard",
        "Annual Summary",
        "CSV / LMS Export"
    ]
)

# =========================
# ADD STUDENT
# =========================
if menu == "Add Student":
    st.header("➕ Add Student")
    name = st.text_input("Student Name")
    if st.button("Save Student"):
        add_student(name)
        st.success("Student added successfully")

# =========================
# ENTER ASSESSMENT
# =========================
if menu == "Enter Assessment":
    st.header("📝 Enter Student Assessment")

    students = get_students()
    student = st.selectbox("Student", students)
    quarter = st.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"])

    col1, col2, col3 = st.columns(3)
    assignment = col1.number_input("Assignment (10)", 0, 10)
    project = col1.number_input("Project (20)", 0, 20)
    attendance = col2.number_input("Attendance (10)", 0, 10)
    quiz = col2.number_input("Quiz (30)", 0, 30)
    final_project = col3.number_input("Final Project (100)", 0, 100)
    research = col3.number_input("Research (30)", 0, 30)

    if st.button("Submit Assessment"):
        total = assignment + project + attendance + quiz + final_project + research
        grade = calculate_grade(total)
        feedback = generate_feedback(total)

        save_assessment((
            student, quarter, assignment, project, attendance,
            quiz, final_project, research, total, grade,
            feedback, datetime.now().isoformat()
        ))

        st.success(f"Saved! Total: {total} | Grade: {grade}")
        st.info(f"AI Feedback: {feedback}")

# =========================
# VIEW RECORDS
# =========================
if menu == "View Records":
    st.header("📋 Student Records")
    df = load_assessments()
    st.dataframe(df)

# =========================
# DASHBOARD
# =========================
if menu == "Analytics Dashboard":
    st.header("📊 Class Analytics")
    df = load_assessments()

    if not df.empty:
        avg = df["total"].mean()
        st.metric("Class Average", round(avg, 2))

        rank_df = df.groupby("student")["total"].sum().reset_index()
        rank_df["Rank"] = rank_df["total"].rank(ascending=False)

        st.subheader("Student Rankings")
        st.dataframe(rank_df.sort_values("Rank"))

        st.bar_chart(rank_df.set_index("student")["total"])
    else:
        st.warning("No data available")

# =========================
# ANNUAL SUMMARY
# =========================
if menu == "Annual Summary":
    st.header("🧾 Annual Performance Summary")
    df = load_assessments()

    if not df.empty:
        summary = df.groupby("student")["total"].sum().reset_index()
        summary["Final Grade"] = summary["total"].apply(calculate_grade)
        st.dataframe(summary)
    else:
        st.warning("No records found")

# =========================
# CSV / LMS EXPORT
# =========================
if menu == "CSV / LMS Export":
    st.header("📥 Export for LMS")
    df = load_assessments()

    if not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV for LMS",
            csv,
            "worla_lms_export.csv",
            "text/csv"
        )
    else:
        st.warning("No data to export")
