import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    conn = psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )
    return conn

def init_db():
    conn = get_connection()
    cur  = conn.cursor()

    # ── Raw jobs from API ────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            company     TEXT,
            location    TEXT,
            country     TEXT,
            salary_min  FLOAT,
            salary_max  FLOAT,
            description TEXT,
            category    TEXT,
            posted_at   TIMESTAMP,
            fetched_at  TIMESTAMP DEFAULT NOW()
        )
    """)

    # ── Master skills list ───────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id         SERIAL PRIMARY KEY,
            name       TEXT UNIQUE NOT NULL
        )
    """)

    # ── Skills per job ───────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_skills (
            job_id     TEXT REFERENCES jobs(id),
            skill_id   INTEGER REFERENCES skills(id),
            PRIMARY KEY (job_id, skill_id)
        )
    """)

    # ── Company insights ─────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id           SERIAL PRIMARY KEY,
            name         TEXT UNIQUE NOT NULL,
            job_count    INTEGER DEFAULT 0,
            avg_salary   FLOAT DEFAULT 0,
            updated_at   TIMESTAMP DEFAULT NOW()
        )
    """)

    # ── Daily skill trends ───────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skill_trends (
            id         SERIAL PRIMARY KEY,
            skill_id   INTEGER REFERENCES skills(id),
            date       DATE DEFAULT CURRENT_DATE,
            count      INTEGER DEFAULT 0,
            UNIQUE(skill_id, date)
        )
    """)

    # ── Fetch history ────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fetch_logs (
            id          SERIAL PRIMARY KEY,
            fetched_at  TIMESTAMP DEFAULT NOW(),
            jobs_fetched INTEGER DEFAULT 0,
            status      TEXT DEFAULT 'success'
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized!")

if __name__ == "__main__":
    init_db()