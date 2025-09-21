import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import wikipedia
import openai

# -------- CONFIG --------
app = Flask(__name__)
DB_NAME = "studentlite.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
openai.api_key = "YOUR_OPENAI_API_KEY"  # Replace with your key

# -------- DB INIT --------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS timetables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    day TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

# -------- FUNCTIONS --------
def fetch_history_questions(country):
    questions = []
    try:
        summary = wikipedia.summary(f"History of {country}", sentences=5)
        for i, sentence in enumerate(summary.split('. ')):
            if sentence.strip():
                questions.append(f"Question {i+1}: {sentence.strip()}?")
    except:
        questions.append(f"Could not fetch History for {country}.")
    return questions

def generate_questions_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful quiz generator."},
            {"role": "user", "content": f"Create 5 quiz questions from the following text:\n{text}"}
        ],
        max_tokens=500
    )
    output = response['choices'][0]['message']['content']
    return [q.strip() for q in output.split('\n') if q.strip()]

# -------- ROUTES --------

# Home
@app.route("/")
def home():
    return render_template("home.html")

# Study Plan
@app.route("/study-plan", methods=["GET", "POST"])
def study_plan():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if request.method == "POST":
        subject = request.form["subject"]
        day = request.form["day"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        c.execute("INSERT INTO timetables (subject, day, start_time, end_time) VALUES (?, ?, ?, ?)",
                  (subject, day, start_time, end_time))
        conn.commit()
    c.execute("SELECT * FROM timetables")
    timetables = c.fetchall()
    conn.close()
    return render_template("study_plan.html", timetables=timetables)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_timetable(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if request.method == "POST":
        subject = request.form["subject"]
        day = request.form["day"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        c.execute("UPDATE timetables SET subject=?, day=?, start_time=?, end_time=? WHERE id=?",
                  (subject, day, start_time, end_time, id))
        conn.commit()
        conn.close()
        return redirect(url_for("study_plan"))
    c.execute("SELECT * FROM timetables WHERE id=?", (id,))
    timetable = c.fetchone()
    conn.close()
    return render_template("edit_timetable.html", timetable=timetable)

@app.route("/delete/<int:id>")
def delete_timetable(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM timetables WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("study_plan"))

# Quiz
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        subject = request.form.get("subject")
        country = request.form.get("country")
        duration = min(10, int(request.form.get("duration", 5)))
        uploaded_file = request.files.get("doc")
        filename = None
        questions = []

        # AI document questions
        if uploaded_file and uploaded_file.filename != "":
            filename = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(filename)
            try:
                doc_questions = generate_questions_from_file(filename)
                questions.extend(doc_questions)
            except:
                questions.append(f"Could not generate questions from {uploaded_file.filename}")

        # History questions
        if subject == "History" and country:
            questions.extend(fetch_history_questions(country))

        if not questions:
            questions.append(f"Sample question for {subject}")

        return render_template("quiz_display.html", questions=questions, duration=duration, subject=subject)

    return render_template("quiz.html")

# Sports
@app.route("/sports")
def sports():
    now = datetime.now()
    current_day = now.strftime("%A")
    current_time = now.strftime("%H:%M")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT subject, day, start_time, end_time FROM timetables")
    timetables = c.fetchall()
    conn.close()

    locked = False
    for subject, day, start, end in timetables:
        if day == current_day and start <= current_time <= end:
            locked = True
            break

    if locked:
        return render_template("sports_locked.html")
    else:
        return render_template("sports.html")

# Dictionary
@app.route("/dictionary")
def dictionary():
    return render_template("dictionary.html")

# -------- RUN --------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
