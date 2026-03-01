from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import sqlite3
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

app = FastAPI()   # ← MUST BE HERE (move this up)

conn = sqlite3.connect("skill_gap.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    role TEXT,
    match_percentage REAL,
    fit_level TEXT
)
""")

conn.commit()
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
class Employee(BaseModel):
    name: str
    role: str
    skills: List[str]

# Role-based skill requirements
ROLE_SKILLS = {
    "backend developer": {"python", "api", "sql"},
    "frontend developer": {"html", "css", "javascript", "react"},
    "data analyst": {"python", "sql", "excel", "power bi"},
    "ai engineer": {"python", "machine learning", "tensorflow", "pytorch"}
}
SKILL_RECOMMENDATIONS = {
    "python": "Build backend projects using FastAPI or Django.",
    "sql": "Practice writing queries and joins using MySQL or PostgreSQL.",
    "api": "Learn REST API design and build small API services.",
    "problem solving": "Solve DSA problems daily on LeetCode or CodeStudio.",
    "html": "Build static web pages.",
    "css": "Practice layouts using Flexbox and Grid.",
    "javascript": "Build interactive web apps.",
    "react": "Create frontend projects using React.",
    "excel": "Learn pivot tables and data analysis.",
    "statistics": "Study probability and basic statistics concepts.",
    "power bi": "Build dashboards and practice DAX formulas.",
    "machine learning": "Learn ML fundamentals and implement models using scikit-learn.",
    "tensorflow": "Build neural network models using TensorFlow.",
    "pytorch": "Practice deep learning models using PyTorch."
}


from fastapi import Form

@app.post("/analyze", response_class=HTMLResponse)
def analyze(
    request: Request,
    name: str = Form(...),
    role: str = Form(...),
    skills: str = Form(...)
):
    skill_list = [s.strip().lower() for s in skills.split(",")]

    required_skills = ROLE_SKILLS.get(role.strip().lower(), set())

    matched = list(set(skill_list) & required_skills)
    missing = list(required_skills - set(skill_list))

    match_percentage = int((len(matched) / len(required_skills)) * 100) if required_skills else 0
    if match_percentage >= 80:
        fit_level = "Strong Fit"
    elif match_percentage >= 50:
        fit_level = "Moderate Fit"
    else:
        fit_level = "Weak Fit"
        recommendations = {
            skill: SKILL_RECOMMENDATIONS.get(skill, "Work on improving this skill.")
            for skill in missing
        }

    return templates.TemplateResponse("result.html", {
        "request": request,
        "name": name,
        "role": role,
        "matched": matched,
        "missing": missing,
        "percentage": match_percentage,
        "fit_level": fit_level,
        "recommendations": recommendations
    })
    cursor.execute("""
                   INSERT INTO analysis_history (name, role, match_percentage, fit_level)
                   VALUES (?, ?, ?, ?)
                   """, (employee.name, employee.role, match_percentage, fit_level))

    conn.commit()
    return {
        "employee": employee.name,
        "role": employee.role,
        "matched_skills": list(matched_skills),
        "missing_skills": list(missing_skills),
        "skill_gap_count": len(missing_skills),
        "match_percentage": match_percentage,
        "fit_level": fit_level,
        "recommendations": recommendations
    }
@app.get("/history")
def get_history():
    cursor.execute("SELECT * FROM analysis_history")
    rows = cursor.fetchall()

    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "name": row[1],
            "role": row[2],
            "match_percentage": row[3],
            "fit_level": row[4]
        })

    return {"analysis_history": history}
@app.delete("/history/{record_id}")
def delete_record(record_id: int):
    cursor.execute("DELETE FROM analysis_history WHERE id = ?", (record_id,))
    conn.commit()

    return {"message": f"Record {record_id} deleted successfully"}
@app.put("/history/{record_id}")
def update_record(record_id: int, updated_data: dict):
    cursor.execute("""
        UPDATE analysis_history
        SET name = ?, role = ?
        WHERE id = ?
    """, (updated_data["name"], updated_data["role"], record_id))

    conn.commit()

    return {"message": f"Record {record_id} updated successfully"}
@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})