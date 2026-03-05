import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from database import get_connection

load_dotenv()

APP_ID  = os.environ.get("ADZUNA_APP_ID")
APP_KEY = os.environ.get("ADZUNA_APP_KEY")

# ── Skills we track ───────────────────────────────────────
# This is our master skills dictionary
# We'll extract these from job descriptions
TRACKED_SKILLS = [
    # Languages
    "python", "javascript", "typescript", "java", "golang",
    "rust", "kotlin", "swift", "scala", "ruby", "php", "c++",
    # Frontend
    "react", "vue", "angular", "nextjs", "html", "css",
    # Backend
    "nodejs", "django", "flask", "fastapi", "spring",
    # Data & AI
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "pandas", "numpy", "scikit-learn", "nlp", "computer vision",
    "llm", "langchain", "openai",
    # Data Engineering
    "sql", "postgresql", "mysql", "mongodb", "redis",
    "elasticsearch", "kafka", "spark", "airflow", "dbt",
    # Cloud
    "aws", "azure", "gcp", "docker", "kubernetes",
    "terraform", "ci/cd", "devops",
    # Tools
    "git", "linux", "agile", "scrum",
]

# ── Job roles we search for ───────────────────────────────
JOB_QUERIES = [
    "python developer",
    "data scientist",
    "machine learning engineer",
    "frontend developer",
    "backend developer",
    "devops engineer",
    "data engineer",
    "AI engineer",
    "full stack developer",
    "cloud engineer",
]

# ── Extract skills from description ───────────────────────
def extract_skills(description):
    """
    Scans job description text for known skills.
    Returns list of skill names found.
    """
    if not description:
        return []

    description_lower = description.lower()
    found_skills      = []

    for skill in TRACKED_SKILLS:
        if skill.lower() in description_lower:
            found_skills.append(skill)

    return found_skills

# ── Save skills to database ───────────────────────────────
def save_skills(cur, job_id, skills):
    """
    Saves skills for a job to the database.
    Creates skill if it doesn't exist yet.
    """
    for skill_name in skills:
        # Insert skill if not exists
        cur.execute("""
            INSERT INTO skills (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, (skill_name,))

        # Get skill id
        cur.execute(
            "SELECT id FROM skills WHERE name = %s",
            (skill_name,)
        )
        skill = cur.fetchone()

        if skill:
            # Link skill to job
            cur.execute("""
                INSERT INTO job_skills (job_id, skill_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (job_id, skill["id"]))

            # Update skill trend for today
            cur.execute("""
                INSERT INTO skill_trends (skill_id, date, count)
                VALUES (%s, CURRENT_DATE, 1)
                ON CONFLICT (skill_id, date)
                DO UPDATE SET count = skill_trends.count + 1
            """, (skill["id"],))

# ── Save company to database ──────────────────────────────
def save_company(cur, company_name, salary_min, salary_max):
    """
    Updates company job count and average salary.
    """
    if not company_name:
        return

    avg_salary = 0
    if salary_min and salary_max:
        avg_salary = (salary_min + salary_max) / 2

    cur.execute("""
        INSERT INTO companies (name, job_count, avg_salary)
        VALUES (%s, 1, %s)
        ON CONFLICT (name) DO UPDATE
        SET job_count  = companies.job_count + 1,
            avg_salary = (companies.avg_salary + %s) / 2,
            updated_at = NOW()
    """, (company_name, avg_salary, avg_salary))

# ── Fetch jobs for one query ──────────────────────────────
def fetch_jobs(query, pages=2):
    """
    Fetches jobs from Adzuna for a given search query.
    pages = how many pages to fetch (10 jobs per page)
    """
    all_jobs = []

    for page in range(1, pages + 1):
        url    = f"https://api.adzuna.com/v1/api/jobs/us/search/{page}"
        params = {
            "app_id":           APP_ID,
            "app_key":          APP_KEY,
            "results_per_page": 10,
            "what":             query,
            "content-type":     "application/json"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            all_jobs.extend(data.get("results", []))
            print(f"  Fetched page {page} for '{query}' → {len(data.get('results', []))} jobs")
        else:
            print(f"  Error fetching '{query}': {response.status_code}")
            break

    return all_jobs

# ── Save jobs to database ─────────────────────────────────
def save_jobs(jobs):
    """
    Saves a list of jobs to the database.
    Extracts and saves skills and company data too.
    """
    conn  = get_connection()
    cur   = conn.cursor()
    saved = 0

    for job in jobs:
        job_id      = job.get("id")
        title       = job.get("title")
        company     = job["company"]["display_name"]
        location    = job["location"]["display_name"]
        country     = job["location"]["area"][0] if job["location"]["area"] else "US"
        salary_min  = job.get("salary_min")
        salary_max  = job.get("salary_max")
        description = job.get("description", "")
        category    = job["category"]["label"]
        posted_at   = job.get("created")

        # Skip if job already exists
        cur.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
        if cur.fetchone():
            continue

        # Save job
        cur.execute("""
            INSERT INTO jobs
            (id, title, company, location, country,
             salary_min, salary_max, description, category, posted_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (job_id, title, company, location, country,
              salary_min, salary_max, description, category, posted_at))

        # Extract and save skills
        skills = extract_skills(description)
        save_skills(cur, job_id, skills)

        # Save company data
        save_company(cur, company, salary_min, salary_max)

        saved += 1

    conn.commit()
    cur.close()
    conn.close()

    return saved

# ── Main fetch function ───────────────────────────────────
def run_fetch():
    """
    Runs the full fetch cycle.
    Fetches all job queries and saves to database.
    """
    conn  = get_connection()
    cur   = conn.cursor()
    total = 0

    print("🔄 Starting job fetch...")

    for query in JOB_QUERIES:
        print(f"\nFetching: {query}")
        jobs  = fetch_jobs(query, pages=2)
        saved = save_jobs(jobs)
        total += saved
        print(f"  Saved {saved} new jobs")

    # Log the fetch
    cur.execute("""
        INSERT INTO fetch_logs (jobs_fetched, status)
        VALUES (%s, 'success')
    """, (total,))

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n✅ Fetch complete! Total new jobs saved: {total}")
    return total

if __name__ == "__main__":
    run_fetch()