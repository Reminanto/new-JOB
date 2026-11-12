from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date
import sqlite3
import os
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-development-key-change-in-render")

# Create the database and tables when the application starts.
init_db()


def login_required(route_function):
    """Allow a page to open only when the user is logged in."""
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return route_function(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in every field.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, password_hash)
                )
            flash("Account created. You can now log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email address is already registered.", "danger")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Incorrect email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]

    with get_db() as db:
        total = db.execute(
            "SELECT COUNT(*) AS count FROM applications WHERE user_id = ?",
            (user_id,)
        ).fetchone()["count"]

        rows = db.execute(
            """SELECT status, COUNT(*) AS count
               FROM applications
               WHERE user_id = ?
               GROUP BY status""",
            (user_id,)
        ).fetchall()

        recent_jobs = db.execute(
            """SELECT * FROM applications
               WHERE user_id = ?
               ORDER BY application_id DESC LIMIT 5""",
            (user_id,)
        ).fetchall()

        upcoming = db.execute(
            """SELECT applications.company_name, applications.job_role,
                      followups.followup_date, followups.description
               FROM followups
               JOIN applications
                 ON applications.application_id = followups.application_id
               WHERE applications.user_id = ?
                 AND followups.followup_date >= ?
               ORDER BY followups.followup_date LIMIT 5""",
            (user_id, date.today().isoformat())
        ).fetchall()

    counts = {
        "Applied": 0,
        "Assessment": 0,
        "Interview": 0,
        "Selected": 0,
        "Rejected": 0,
        "On Hold": 0
    }
    for row in rows:
        counts[row["status"]] = row["count"]

    selected = counts["Selected"]
    success_rate = round((selected / total) * 100, 1) if total else 0

    return render_template(
        "dashboard.html",
        total=total,
        counts=counts,
        success_rate=success_rate,
        recent_jobs=recent_jobs,
        upcoming=upcoming
    )


@app.route("/applications")
@login_required
def applications():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    user_id = session["user_id"]

    sql = "SELECT * FROM applications WHERE user_id = ?"
    values = [user_id]

    if search:
        sql += " AND (company_name LIKE ? OR job_role LIKE ?)"
        values.extend([f"%{search}%", f"%{search}%"])

    if status:
        sql += " AND status = ?"
        values.append(status)

    sql += " ORDER BY application_id DESC"

    with get_db() as db:
        jobs = db.execute(sql, values).fetchall()

    return render_template("applications.html", jobs=jobs, search=search, selected_status=status)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_job():
    if request.method == "POST":
        company = request.form.get("company_name", "").strip()
        role = request.form.get("job_role", "").strip()
        applied_date = request.form.get("applied_date", "")
        status = request.form.get("status", "Applied")
        location = request.form.get("location", "").strip()
        salary = request.form.get("salary", "").strip()
        notes = request.form.get("notes", "").strip()

        allowed_statuses = ["Applied", "Assessment", "Interview", "Selected", "Rejected", "On Hold"]

        if not company or not role or not applied_date:
            flash("Company, job role, and application date are required.", "danger")
            return redirect(url_for("add_job"))

        if status not in allowed_statuses:
            flash("Please choose a valid application status.", "danger")
            return redirect(url_for("add_job"))

        try:
            salary_value = float(salary) if salary else None
            if salary_value is not None and salary_value < 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid non-negative salary.", "danger")
            return redirect(url_for("add_job"))

        with get_db() as db:
            db.execute(
                """INSERT INTO applications
                   (user_id, company_name, job_role, applied_date, status, location, salary, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (session["user_id"], company, role, applied_date, status, location,
                 salary_value, notes)
            )

        flash("Job application added successfully.", "success")
        return redirect(url_for("applications"))

    return render_template("add_job.html", today=date.today().isoformat())


@app.route("/edit/<int:job_id>", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    user_id = session["user_id"]

    with get_db() as db:
        job = db.execute(
            "SELECT * FROM applications WHERE application_id = ? AND user_id = ?",
            (job_id, user_id)
        ).fetchone()

        if job is None:
            flash("Application not found.", "danger")
            return redirect(url_for("applications"))

        if request.method == "POST":
            company = request.form.get("company_name", "").strip()
            role = request.form.get("job_role", "").strip()
            applied_date = request.form.get("applied_date", "")
            status = request.form.get("status", "Applied")
            location = request.form.get("location", "").strip()
            salary = request.form.get("salary", "").strip()
            notes = request.form.get("notes", "").strip()
            allowed_statuses = ["Applied", "Assessment", "Interview", "Selected", "Rejected", "On Hold"]

            if not company or not role or not applied_date or status not in allowed_statuses:
                flash("Please check the required fields.", "danger")
                return redirect(url_for("edit_job", job_id=job_id))

            try:
                salary_value = float(salary) if salary else None
                if salary_value is not None and salary_value < 0:
                    raise ValueError
            except ValueError:
                flash("Please enter a valid non-negative salary.", "danger")
                return redirect(url_for("edit_job", job_id=job_id))

            db.execute(
                """UPDATE applications
                   SET company_name = ?, job_role = ?, applied_date = ?, status = ?,
                       location = ?, salary = ?, notes = ?
                   WHERE application_id = ? AND user_id = ?""",
                (company, role, applied_date, status, location, salary_value,
                 notes, job_id, user_id)
            )
            flash("Application updated.", "success")
            return redirect(url_for("applications"))

    return render_template("edit_job.html", job=job)


@app.route("/delete/<int:job_id>", methods=["POST"])
@login_required
def delete_job(job_id):
    with get_db() as db:
        # The user_id condition prevents one user deleting another user's record.
        db.execute(
            "DELETE FROM applications WHERE application_id = ? AND user_id = ?",
            (job_id, session["user_id"])
        )
    flash("Application deleted.", "success")
    return redirect(url_for("applications"))


@app.route("/followup/add/<int:job_id>", methods=["GET", "POST"])
@login_required
def add_followup(job_id):
    user_id = session["user_id"]

    with get_db() as db:
        job = db.execute(
            "SELECT * FROM applications WHERE application_id = ? AND user_id = ?",
            (job_id, user_id)
        ).fetchone()

        if job is None:
            flash("Application not found.", "danger")
            return redirect(url_for("applications"))

        if request.method == "POST":
            followup_date = request.form.get("followup_date", "")
            description = request.form.get("description", "").strip()

            if not followup_date:
                flash("Please select a follow-up date.", "danger")
                return redirect(url_for("add_followup", job_id=job_id))

            db.execute(
                """INSERT INTO followups (application_id, followup_date, description)
                   VALUES (?, ?, ?)""",
                (job_id, followup_date, description)
            )

            flash("Follow-up reminder added.", "success")
            return redirect(url_for("dashboard"))

    return render_template("followup.html", job=job)


if __name__ == "__main__":
    app.run(debug=True)
