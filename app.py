from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, render_template, jsonify
from database import get_connection, init_db
from analyser import (
    get_top_skills,
    get_skill_trends,
    get_top_companies,
    get_salary_by_role,
    get_salary_by_skill,
    get_jobs_by_category,
    get_dashboard_summary
)

app = Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)

# Safe startup — don't crash if DB not ready
try:
    init_db()
    print("✅ Database initialized!")
except Exception as e:
    print(f"⚠️ Database init failed: {e}")

# ── Dashboard ─────────────────────────────────────────────
@app.route("/")
def dashboard():
    summary    = get_dashboard_summary()
    top_skills = get_top_skills(10)
    companies  = get_top_companies(5)
    categories = get_jobs_by_category()
    return render_template("dashboard.html",
        summary    = summary,
        top_skills = top_skills,
        companies  = companies,
        categories = categories
    )

# ── Skills Page ───────────────────────────────────────────
@app.route("/skills")
def skills():
    top_skills = get_top_skills(20)
    salary_by_skill = get_salary_by_skill(15)
    return render_template("skills.html",
        top_skills      = top_skills,
        salary_by_skill = salary_by_skill
    )

# ── Salaries Page ─────────────────────────────────────────
@app.route("/salaries")
def salaries():
    salary_by_role  = get_salary_by_role(10)
    salary_by_skill = get_salary_by_skill(15)
    return render_template("salaries.html",
        salary_by_role  = salary_by_role,
        salary_by_skill = salary_by_skill
    )

# ── Companies Page ────────────────────────────────────────
@app.route("/companies")
def companies():
    companies = get_top_companies(20)
    return render_template("companies.html",
        companies = companies
    )

# ── API Endpoints (for charts) ────────────────────────────
@app.route("/api/top-skills")
def api_top_skills():
    return jsonify(get_top_skills(20))

@app.route("/api/companies")
def api_companies():
    return jsonify(get_top_companies(10))

@app.route("/api/salary-by-skill")
def api_salary_by_skill():
    return jsonify(get_salary_by_skill(15))

@app.route("/api/categories")
def api_categories():
    return jsonify(get_jobs_by_category())

@app.route("/debug")
def debug():
    import os
    db_url = os.environ.get("DATABASE_URL", "NOT FOUND")
    return {
        "url_found": db_url != "NOT FOUND",
        "url_preview": db_url[:50] if db_url else "empty",
        "starts_with_postgresql": db_url.startswith("postgresql") if db_url else False
    }

@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(debug=True)