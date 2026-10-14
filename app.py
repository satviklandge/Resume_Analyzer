from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import models  # registers User & Reports with SQLAlchemy
from db import engine, Base, sessionLocal
from ai import analyze_resume
import PyPDF2
import docx
import json
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash

# Load env variables
load_dotenv()

# Create all tables in DB if they don't exist
Base.metadata.create_all(bind=engine)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.getenv("app.secret_key") or "ai-chatbot-secure-secret-key-2026"

# ── Home ────────────────────────────────────────────────────────────────────
@app.route('/')
def Home():
    if "user" in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ── Signup ──────────────────────────────────────────────────────────────────
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if "user" in session:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email",    "").strip().lower()
        password = request.form.get("password", "")

        # ── Server-side validation ──────────────────────────────────────────
        if not username:
            return render_template('signup.html', error="Username is required.")
        if len(username) < 3:
            return render_template('signup.html', error="Username must be at least 3 characters.")
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return render_template('signup.html', error="Please enter a valid email address.")
        if not password or len(password) < 8:
            return render_template('signup.html', error="Password must be at least 8 characters.")

        db = sessionLocal()
        try:
            existing_email = db.query(models.User).filter_by(email=email).first()
            if existing_email:
                return render_template('signup.html',
                    error="An account with this email already exists. Please log in.")

            existing_username = db.query(models.User).filter_by(username=username).first()
            if existing_username:
                return render_template('signup.html',
                    error="This username is already taken. Please choose another.")

            hashed_pw = generate_password_hash(password)
            user = models.User(email=email, password=hashed_pw, username=username)
            db.add(user)
            db.commit()
        finally:
            db.close()

        return redirect(url_for('login'))

    return render_template('signup.html')

# ── Login ───────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if "user" in session:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        email    = request.form.get("email",    "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template('login.html', error="Please fill in all fields.")

        db = sessionLocal()
        user = None
        try:
            user = db.query(models.User).filter_by(email=email).first()
        finally:
            db.close()

        if user and check_password_hash(user.password, password):
            session["user"] = user.id
            session["username"] = user.username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html',
                error="Invalid email or password. Please try again.")

    return render_template('login.html')

# ── Dashboard ───────────────────────────────────────────────────────────────
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if "user" not in session:
        return redirect(url_for('login'))

    analysis_result = None
    target_role = ""
    error_message = None

    if request.method == "POST":
        target_role = request.form.get("Role", "").strip()
        pasted_text = request.form.get("resume_text", "").strip()
        file        = request.files.get("file")
        resume_text = ""

        # ── 1. Process uploaded file if present ──────────────────────────────
        if file and file.filename != "":
            filename_lower = file.filename.lower()
            if filename_lower.endswith('.pdf'):
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    extracted = ""
                    for page in pdf_reader.pages:
                        extracted += (page.extract_text() or "") + "\n"
                    resume_text = extracted.strip()
                except Exception as e:
                    error_message = f"Error reading PDF file: {str(e)}"
            elif filename_lower.endswith('.docx'):
                try:
                    doc = docx.Document(file)
                    extracted = ""
                    for para in doc.paragraphs:
                        extracted += para.text + "\n"
                    resume_text = extracted.strip()
                except Exception as e:
                    error_message = f"Error reading DOCX file: {str(e)}"
            else:
                error_message = "Invalid file format. Please upload a .pdf or .docx file."

        # ── 2. Fall back to pasted text if no file extracted ────────────────
        if not resume_text and pasted_text:
            resume_text = pasted_text

        # ── 3. Validate Inputs ──────────────────────────────────────────────
        if not error_message:
            if not target_role:
                error_message = "Please specify the target job role or career goal."
            elif not resume_text:
                error_message = "Please paste your resume content or upload a PDF/DOCX file."

        # ── 4. Perform AI Analysis & Persist ────────────────────────────────
        if not error_message and resume_text and target_role:
            try:
                analysis_result = analyze_resume(resume_text, target_role)

                # Persist to database
                db = sessionLocal()
                try:
                    user_record = db.query(models.User).filter_by(id=session.get("user")).first()
                    if user_record:
                        # Pack target_role inside the report data for rich display in history
                        saved_payload = {
                            "target_role": target_role,
                            "analysis": analysis_result
                        }
                        report = models.Reports(
                            user_id=user_record.id,
                            resume_text=resume_text,
                            resume_summary=json.dumps(saved_payload)
                        )
                        db.add(report)
                        db.commit()
                finally:
                    db.close()

            except Exception as e:
                error_message = f"An unexpected error occurred during analysis: {str(e)}"

    return render_template(
        'dashboard.html',
        username=session.get("username", "User"),
        analysis=analysis_result,
        target_role=target_role,
        error=error_message
    )

# ── History ──────────────────────────────────────────────────────────────────
@app.route('/history')
def history():
    if "user" not in session:
        return redirect(url_for('login'))

    db = sessionLocal()
    parsed_reports = []
    try:
        user_record = db.query(models.User).filter_by(id=session.get("user")).first()
        if not user_record:
            return redirect(url_for('login'))

        reports = db.query(models.Reports).filter_by(user_id=user_record.id).order_by(models.Reports.id.desc()).all()

        for report in reports:
            raw_summary = report.resume_summary
            role = "Career Analysis"
            analysis_data = None

            try:
                parsed_json = json.loads(raw_summary)
                if isinstance(parsed_json, dict):
                    if "analysis" in parsed_json:
                        role = parsed_json.get("target_role", "Target Role")
                        analysis_data = parsed_json.get("analysis")
                    else:
                        analysis_data = parsed_json
                elif isinstance(parsed_json, (list, tuple)):
                    # Legacy structure (resume_text, user_goal)
                    if len(parsed_json) >= 2:
                        role = parsed_json[1]
                    analysis_data = {"overall_feedback": str(parsed_json)}
                else:
                    analysis_data = {"overall_feedback": str(raw_summary)}
            except Exception:
                analysis_data = {"overall_feedback": str(raw_summary)}

            parsed_reports.append({
                "id": report.id,
                "resume_preview": report.resume_text[:200] + ("..." if len(report.resume_text) > 200 else ""),
                "full_resume": report.resume_text,
                "target_role": role,
                "analysis": analysis_data
            })
    finally:
        db.close()

    return render_template('history.html', reports=parsed_reports, username=session.get("username", "User"))

# ── Logout ───────────────────────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Forgot Password ───────────────────────────────────────────────────────────
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    message = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if email and re.match(r"[^@]+@[^@]+\.[^@]+", email):
            message = (
                f"If an account with '{email}' exists, "
                "a password reset link has been dispatched to your inbox."
            )
        else:
            message = "Please enter a valid email address."
    return render_template('forgot_password.html', message=message)


if __name__ == '__main__':
    app.run(debug=True, port=5000)