import os
from dotenv import load_dotenv
from database import get_connection

load_dotenv()

# ── Top Skills ────────────────────────────────────────────
def get_top_skills(limit=20, days=30):
    """
    Returns most demanded skills in the last N days.
    """
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT
            s.name,
            COUNT(js.job_id) as demand
        FROM skills s
        JOIN job_skills js ON js.skill_id = s.id
        JOIN jobs j ON j.id = js.job_id
        WHERE j.fetched_at > NOW() - INTERVAL '%s days'
        GROUP BY s.name
        ORDER BY demand DESC
        LIMIT %s
    """, (days, limit))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in results]

# ── Skill Trends Over Time ────────────────────────────────
def get_skill_trends(skill_names):
    """
    Returns daily count for given skills over time.
    Used for trend charts.
    """
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT
            s.name,
            st.date,
            st.count
        FROM skill_trends st
        JOIN skills s ON s.id = st.skill_id
        WHERE s.name = ANY(%s)
        ORDER BY st.date ASC
    """, (skill_names,))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in results]

# ── Top Companies ─────────────────────────────────────────
def get_top_companies(limit=10):
    """
    Returns companies with most job postings.
    """
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT
            name,
            job_count,
            ROUND(avg_salary::numeric, 0) as avg_salary
        FROM companies
        ORDER BY job_count DESC
        LIMIT %s
    """, (limit,))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in results]

# ── Salary by Role ────────────────────────────────────────
def get_salary_by_role(limit=10):
    """
    Returns average salary for each job category.
    Only includes jobs with salary data.
    """
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT
            category,
            ROUND(AVG(salary_min)::numeric, 0) as avg_min,
            ROUND(AVG(salary_max)::numeric, 0) as avg_max,
            COUNT(*) as job_count
        FROM jobs
        WHERE salary_min IS NOT NULL
        AND salary_min > 0
        GROUP BY category
        ORDER BY avg_min DESC
        LIMIT %s
    """, (limit,))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in results]

# ── Salary by Skill ───────────────────────────────────────
def get_salary_by_skill(limit=15):
    """
    Returns average salary for jobs requiring each skill.
    """
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT
            s.name,
            ROUND(AVG(j.salary_min)::numeric, 0) as avg_salary,
            COUNT(j.id) as job_count
        FROM skills s
        JOIN job_skills js ON js.skill_id = s.id
        JOIN jobs j ON j.id = js.job_id
        WHERE j.salary_min IS NOT NULL
        AND j.salary_min > 0
        GROUP BY s.name
        HAVING COUNT(j.id) > 2
        ORDER BY avg_salary DESC
        LIMIT %s
    """, (limit,))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in results]

# ── Job Count by Category ─────────────────────────────────
def get_jobs_by_category():
    """
    Returns job count per category.
    Used for pie/bar charts.
    """
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT
            category,
            COUNT(*) as count
        FROM jobs
        GROUP BY category
        ORDER BY count DESC
    """)

    results = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in results]

# ── Dashboard Summary ─────────────────────────────────────
def get_dashboard_summary():
    """
    Returns key numbers for the dashboard header.
    """
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) as total FROM jobs")
    total_jobs = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM skills")
    total_skills = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM companies")
    total_companies = cur.fetchone()["total"]

    cur.execute("""
        SELECT ROUND(AVG(salary_min)::numeric, 0) as avg
        FROM jobs
        WHERE salary_min IS NOT NULL
        AND salary_min > 0
    """)
    avg_salary = cur.fetchone()["avg"]

    cur.execute("""
        SELECT fetched_at FROM fetch_logs
        ORDER BY fetched_at DESC LIMIT 1
    """)
    last_fetch = cur.fetchone()

    cur.close()
    conn.close()

    return {
        "total_jobs":      total_jobs,
        "total_skills":    total_skills,
        "total_companies": total_companies,
        "avg_salary":      avg_salary,
        "last_fetch":      last_fetch["fetched_at"] if last_fetch else None
    }

if __name__ == "__main__":
    print("📊 Testing analyser...\n")

    print("Top 10 Skills:")
    for s in get_top_skills(10):
        print(f"  {s['name']:20} → {s['demand']} jobs")

    print("\nTop 5 Companies:")
    for c in get_top_companies(5):
        print(f"  {c['name']:30} → {c['job_count']} jobs")

    print("\nSalary by Role:")
    for r in get_salary_by_role(5):
        print(f"  {r['category']:20} → ${r['avg_min']:,} - ${r['avg_max']:,}")

    print("\nDashboard Summary:")
    summary = get_dashboard_summary()
    for k, v in summary.items():
        print(f"  {k}: {v}")