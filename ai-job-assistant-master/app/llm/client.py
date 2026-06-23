"""LLM client wrapper — Gemini (primary) or OpenAI (fallback)."""

import json
import logging
import re
from typing import Iterable

from config import get_settings

log = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    """Parse JSON from LLM output, stripping markdown fences if present."""
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    return json.loads(cleaned)


def _call_gemini(system: str, user: str) -> str:
    import google.generativeai as genai

    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to .env")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        settings.model,
        system_instruction=system,
    )
    response = model.generate_content(
        user,
        generation_config={
            "temperature": 0.3,
            "response_mime_type": "application/json",
        },
    )
    return response.text


def _call_openai(system: str, user: str) -> str:
    from openai import OpenAI

    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Add it to .env")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.model if settings.model.startswith("gpt") else "gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or "{}"


def _is_quota_error(error: Exception) -> bool:
    message = str(error).lower()
    return "quota exceeded" in message or "resourceexhausted" in error.__class__.__name__.lower()


def _extract_prompt_value(user: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}:\s*(.*)", user)
    return match.group(1).strip() if match else ""


def _extract_block(user: str, start_marker: str, end_marker: str) -> str:
    pattern = rf"{re.escape(start_marker)}\n(.*?){re.escape(end_marker)}"
    match = re.search(pattern, user, re.DOTALL)
    return match.group(1).strip() if match else ""


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _infer_candidate_name(resume_text: str) -> str | None:
    for line in resume_text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if any(token in candidate.lower() for token in ["resume", "skills", "projects", "education"]):
            continue
        if len(candidate.split()) <= 4 and any(char.isalpha() for char in candidate):
            return candidate
        break
    return None


def _find_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for keyword in keywords:
        if keyword.lower() in lowered and keyword not in found:
            found.append(keyword)
    return found


def _role_skills(target_role: str) -> list[str]:
    role = target_role.lower()
    mapping: list[tuple[str, list[str]]] = [
        ("python", ["Python", "FastAPI", "Flask", "Django", "SQL", "pytest", "Docker"]),
        ("java", ["Java", "Spring Boot", "SQL", "Docker", "Git", "REST APIs"]),
        ("react", ["JavaScript", "TypeScript", "React", "HTML", "CSS", "REST APIs"]),
        ("backend", ["Python", "FastAPI", "SQL", "REST APIs", "Docker", "AWS"]),
        ("data", ["Python", "SQL", "Pandas", "NumPy", "Excel", "Power BI", "Tableau"]),
        ("devops", ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS", "Git"]),
        ("cloud", ["AWS", "GCP", "Azure", "Docker", "Linux", "CI/CD"]),
        ("mobile", ["Android", "Kotlin", "Java", "Git", "REST APIs"]),
        ("qa", ["pytest", "Selenium", "Postman", "API testing", "CI/CD", "Git"]),
        ("security", ["Linux", "Networking", "Python", "SIEM", "OWASP", "Git"]),
    ]
    for key, skills in mapping:
        if key in role:
            return skills
    return ["Python", "SQL", "Git", "REST APIs", "Docker"]


def _build_analysis_fallback(user: str) -> dict:
    target_role = _extract_prompt_value(user, "Target role") or "Target role"
    resume_text = _extract_block(user, "Resume text:\n---", "---")
    candidate_name = _infer_candidate_name(resume_text)
    skills_found = _find_keywords(
        resume_text,
        [
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "React",
            "Node.js",
            "FastAPI",
            "Flask",
            "Django",
            "SQL",
            "PostgreSQL",
            "MySQL",
            "MongoDB",
            "Docker",
            "Kubernetes",
            "Git",
            "Linux",
            "AWS",
            "GCP",
            "Azure",
            "CI/CD",
            "HTML",
            "CSS",
            "Pandas",
            "NumPy",
            "pytest",
            "REST APIs",
        ],
    )
    role_skills = _role_skills(target_role)
    skill_gaps = [skill for skill in role_skills if skill not in skills_found][:5]
    strengths: list[str] = []
    if "project" in resume_text.lower():
        strengths.append("Includes project experience")
    if len(skills_found) >= 3:
        strengths.append("Shows a relevant technical stack")
    if any(char.isdigit() for char in resume_text):
        strengths.append("Uses concrete details and measurable signals")
    if not strengths:
        strengths.append("Presents a baseline profile that can be improved with stronger role-specific keywords")

    score = 42 + min(len(skills_found) * 5, 25) + (8 if "project" in resume_text.lower() else 0) - len(skill_gaps) * 3
    score = max(20, min(92, score))

    feedback = (
        f"Your resume is a workable starting point for {target_role}, but it still needs stronger role-specific evidence. "
        f"I found {', '.join(skills_found) if skills_found else 'few explicit technical keywords'}, while the main gaps are {', '.join(skill_gaps) if skill_gaps else 'less about skills and more about impact wording'}. "
        f"Tighten the project bullets, add measurable outcomes, and mirror keywords from the job description so the ATS can match your profile more confidently. "
        f"If you add one focused project and quantify the impact of your work, the application will read as much stronger for recruiter screening."
    )

    return {
        "candidate_name": candidate_name,
        "target_role": target_role,
        "ats_score": score,
        "ats_feedback": feedback,
        "skills_found": skills_found,
        "skill_gaps": skill_gaps,
        "strengths": strengths,
    }


def _build_project_suggestions(target_role: str, skill_gaps: list[str]) -> list[dict]:
    primary_gap = skill_gaps[0] if skill_gaps else "deployment"
    secondary_gap = skill_gaps[1] if len(skill_gaps) > 1 else "testing"
    role = target_role.lower()

    if "python" in role or "backend" in role:
        return [
            {
                "title": "Production-Ready Task Tracker API",
                "why": f"Build a REST API with authentication, validation, and logging to show backend fundamentals while addressing {primary_gap}.",
                "stack": ["Python", "FastAPI", "SQL", "Docker"],
                "difficulty": "intermediate",
            },
            {
                "title": "Resume Keyword Analyzer",
                "why": f"Create a tool that scores resumes against role descriptions so you can demonstrate NLP-lite parsing and improve {secondary_gap}.",
                "stack": ["Python", "FastAPI", "Regex", "SQLite"],
                "difficulty": "beginner",
            },
            {
                "title": "Deployed Portfolio Dashboard",
                "why": "Ship a small dashboard with charts, auth, and cloud deployment to prove you can take a project end to end.",
                "stack": ["Python", "JavaScript", "Docker", "AWS"],
                "difficulty": "intermediate",
            },
        ]

    if "data" in role:
        return [
            {
                "title": "Hiring Funnel Analytics Dashboard",
                "why": f"Use SQL and Python to analyse hiring data and show how you can work through {primary_gap} with real datasets.",
                "stack": ["Python", "SQL", "Pandas", "Power BI"],
                "difficulty": "intermediate",
            },
            {
                "title": "ETL Pipeline for Resume Data",
                "why": f"Build a pipeline that cleans and loads structured data so you can demonstrate data engineering basics and strengthen {secondary_gap}.",
                "stack": ["Python", "SQL", "Docker", "Airflow"],
                "difficulty": "intermediate",
            },
            {
                "title": "Interview Prep Recommendation Engine",
                "why": "Show that you can turn raw data into actionable recommendations with a simple scoring model and dashboard.",
                "stack": ["Python", "Pandas", "Streamlit", "SQLite"],
                "difficulty": "beginner",
            },
        ]

    return [
        {
            "title": f"{target_role} Portfolio Project 1",
            "why": f"This project highlights your core strengths while directly addressing {primary_gap}.",
            "stack": ["Python", "Git", "SQL"],
            "difficulty": "beginner",
        },
        {
            "title": f"{target_role} Portfolio Project 2",
            "why": f"This project gives you a concrete story about problem solving and helps close the gap in {secondary_gap}.",
            "stack": ["Python", "Docker", "REST APIs"],
            "difficulty": "intermediate",
        },
        {
            "title": f"{target_role} Portfolio Project 3",
            "why": "This project shows practical end-to-end delivery and gives you a strong demo for interviews.",
            "stack": ["Git", "Testing", "Deployment"],
            "difficulty": "intermediate",
        },
    ]


def _build_mock_interview(target_role: str, skills_found: list[str], skill_gaps: list[str], strengths: list[str]) -> list[dict]:
    focus_skill = skills_found[0] if skills_found else "your strongest technical skill"
    gap_skill = skill_gaps[0] if skill_gaps else "a missing production skill"
    strength = strengths[0] if strengths else "a project you completed"

    questions = [
        {
            "question": f"Tell me about {strength.lower()} and how it prepared you for {target_role} roles.",
            "sample_answer": f"I focused on {strength.lower()} because it helped me understand how to build something practical from start to finish. I planned the work, implemented the core features, and tested the result carefully. The experience taught me how to break a problem into smaller pieces and communicate progress clearly. That same approach would help me contribute quickly in a {target_role} team.",
            "explanation": "Interviewers use this to see whether you can turn past work into a concise, relevant story. A strong answer connects the project to the target role, highlights ownership, and shows how you think through execution. Avoid listing features only; explain decisions, trade-offs, and what you learned. This is also where you can show communication quality and reflection.",
        },
        {
            "question": f"Which technical fundamentals would you review first before working on a {target_role} project?",
            "sample_answer": f"I would first review {focus_skill} fundamentals, then make sure I understand how the data flows through the application. I would also revisit debugging, testing, and the deployment path so I can ship changes safely. If the project uses {gap_skill}, I would practice that area until I could explain it clearly. My goal is to be comfortable with both the implementation and the reasoning behind it.",
            "explanation": "This checks whether the candidate can self-assess gaps and prioritise learning. Interviewers want evidence of structure, not memorised buzzwords. Strong answers show how you connect fundamentals to real work. The best responses are specific about what you would study and why.",
        },
        {
            "question": "Describe a bug you found while building a project and how you fixed it.",
            "sample_answer": "While building a project, I found that one part of the workflow was failing silently when the input format changed. I traced the issue by checking logs, reproducing the problem with a smaller test case, and verifying each step of the pipeline. After fixing the logic, I added a regression test so the same issue would not come back. That process made me more disciplined about debugging and validation.",
            "explanation": "This question measures troubleshooting skill and maturity. A good answer shows a repeatable debugging process, not just the final fix. Mention logs, reproducibility, and testing because those are signals of engineering discipline. Interviewers also look for whether you learned to prevent the bug from returning.",
        },
        {
            "question": "How do you decide between speed and code quality when deadlines are tight?",
            "sample_answer": "I try to ship the smallest useful version first, but I still protect the core path with tests and simple structure. If the deadline is tight, I would reduce scope rather than cut corners on the parts that would be hard to repair later. I would also communicate risks early so the team can make informed trade-offs. That way we move quickly without creating avoidable technical debt.",
            "explanation": "This is a judgement question about pragmatism and collaboration. Interviewers want to see that you can balance delivery pressure with maintainability. Strong answers mention scope control, risk communication, and protecting the critical path. Avoid saying you would just work faster without changing the plan.",
        },
        {
            "question": f"What does good performance look like in a {target_role} project?",
            "sample_answer": "Good performance means the user gets a responsive experience and the system stays reliable as usage grows. I would watch response times, avoid unnecessary work in the hot path, and make sure the data flow is efficient. If the project grows, I would profile the slowest parts instead of guessing. Performance is not just about speed; it is also about predictable behavior and easier maintenance.",
            "explanation": "This probes whether the candidate thinks beyond feature completion. A strong answer touches latency, reliability, and observability. If the role is technical, interviewers expect you to know that performance is measured and improved with evidence. Mention profiling or monitoring to show a practical mindset.",
        },
        {
            "question": f"How would you improve your profile for a {target_role} interview in the next two weeks?",
            "sample_answer": f"I would spend the first few days closing the biggest gap in {gap_skill}, then build one small project that demonstrates it clearly. After that, I would practice explaining the project, the trade-offs I made, and the mistakes I fixed. I would also review common interview questions around {focus_skill} and basic problem solving. My goal would be to leave the next interview with stronger examples and clearer explanations.",
            "explanation": "This question checks whether the candidate has a realistic improvement plan. Strong answers are specific, time-bound, and tied to the actual resume gaps. Interviewers like to hear that you can prioritise the highest-return work first. Keep the answer grounded in observable actions.",
        },
        {
            "question": "Tell me about a time you worked with incomplete requirements.",
            "sample_answer": "When requirements were unclear, I first wrote down the assumptions I was making and validated them with the person requesting the work. I built the simplest version that satisfied the likely core need and kept the implementation flexible enough to adjust later. That reduced rework and kept the discussion focused on the outcome rather than the implementation details. I learned that clarification early saves a lot of time later.",
            "explanation": "This is a behavioural question about collaboration and ambiguity. Interviewers want to see structured communication and good judgement. A strong answer shows that you ask clarifying questions, document assumptions, and iterate safely. Avoid implying that vague requirements are always someone else’s fault.",
        },
        {
            "question": f"Which part of the {target_role} stack would you like to deepen next and why?",
            "sample_answer": f"I would deepen {gap_skill} because it would make my projects more complete and help me work more confidently in production. I already understand the basic flow, but I want to get better at using it in a real application with testing and deployment. That would improve both my technical depth and the quality of the demos I can show. I like learning skills that immediately make my projects stronger.",
            "explanation": "This tests whether the candidate is self-aware and growth-oriented. Good answers name a specific area and connect it to real project work. Interviewers prefer candidates who can explain why a skill matters, not just say they want to learn everything. Keep the response focused and practical.",
        },
        {
            "question": "How do you explain a technical project to a non-technical person?",
            "sample_answer": "I start with the problem the project solves and the value it creates for the user. Then I explain the workflow in simple language and use one or two concrete examples instead of technical jargon. If needed, I can go deeper later, but I prefer to begin with the outcome. That makes the explanation easier to follow and keeps the listener engaged.",
            "explanation": "Interviewers often use this to assess clarity of communication. Strong candidates can adjust the level of detail to the audience. The best answers lead with the user problem, then the solution, then the technical details if asked. Avoid jargon-heavy explanations that hide the value of the work.",
        },
        {
            "question": "Why should we hire you for this role?",
            "sample_answer": f"You should hire me because I am building the right mix of fundamentals, project experience, and willingness to learn quickly. I can talk clearly about what I have built, what I still need to improve, and how I close those gaps. I take feedback seriously and use it to make my work stronger. I would bring steady execution, curiosity, and a practical mindset to the team.",
            "explanation": "This is the closing question and it tests confidence plus self-awareness. Good answers are concise but specific. You should connect strengths to the role and show that you are coachable. Avoid sounding generic; the answer should feel grounded in your real experience.",
        },
    ]

    return questions[:10]


def _local_fallback_json(system: str, user: str) -> str:
    if "Resume text:" in user:
        payload = _build_analysis_fallback(user)
    else:
        target_role = _extract_prompt_value(user, "Target role") or "Target role"
        skills_found = _split_csv(_extract_prompt_value(user, "- Skills found"))
        skill_gaps = _split_csv(_extract_prompt_value(user, "- Skill gaps"))
        strengths = _split_csv(_extract_prompt_value(user, "- Strengths"))
        payload = {
            "project_suggestions": _build_project_suggestions(target_role, skill_gaps),
            "mock_interview": _build_mock_interview(target_role, skills_found, skill_gaps, strengths),
        }
    return json.dumps(payload)


def complete_json(system: str, user: str) -> dict:
    """Call the configured LLM and return parsed JSON. Retries once on parse failure."""
    settings = get_settings()
    caller = _call_openai if settings.llm_provider == "openai" else _call_gemini

    last_error = None
    for attempt in range(2):
        try:
            raw = caller(system, user)
            return _extract_json(raw)
        except Exception as error:
            if settings.llm_provider == "gemini" and _is_quota_error(error):
                log.warning("Gemini quota exhausted, using fallback response")
                try:
                    return _extract_json(_local_fallback_json(system, user))
                except Exception as fallback_error:
                    last_error = fallback_error
                    break

            if isinstance(error, (json.JSONDecodeError, ValueError)):
                last_error = error
                user = user + "\n\nReturn ONLY valid JSON. No markdown, no extra text."
                log.warning("JSON parse failed (attempt %s), retrying", attempt + 1)
                continue

            last_error = error

    raise ValueError(f"LLM returned invalid JSON: {last_error}")
