"""Prompt templates for resume analysis and interview prep."""

RESUME_ANALYSIS_SYSTEM = """You are an expert career coach for B.Tech students and junior developers in India.
Analyze resumes honestly but encouragingly. Write all output in clear, professional English.
Return ONLY valid JSON matching the schema. Do not wrap JSON in markdown."""

RESUME_ANALYSIS_USER = """Target role: {target_role}

Resume text:
---
{resume_text}
---

Return JSON with this exact structure:
{{
  "candidate_name": "string or null",
  "target_role": "{target_role}",
  "ats_score": 0-100 integer,
  "ats_feedback": "4-6 sentences of detailed, actionable feedback in English. Mention specific resume strengths, weaknesses, missing keywords, formatting issues, and concrete improvements for the target role.",
  "skills_found": ["skill1", "skill2"],
  "skill_gaps": ["gap1", "gap2"],
  "strengths": ["strength1", "strength2"]
}}

Score ATS based on: keywords for the role, project clarity, quantified impact, formatting signals, and relevant skills."""


INTERVIEW_PREP_SYSTEM = """You are a senior technical interviewer and mentor helping junior developers prepare for campus and off-campus interviews.
Write everything in clear, professional English. Be specific and educational.
Return ONLY valid JSON. Do not wrap JSON in markdown."""

INTERVIEW_PREP_USER = """Target role: {target_role}

Resume analysis:
- ATS score: {ats_score}
- Skills found: {skills_found}
- Skill gaps: {skill_gaps}
- Strengths: {strengths}

Return JSON:
{{
  "project_suggestions": [
    {{
      "title": "Project name",
      "why": "2-3 sentences explaining why this project closes skill gaps and impresses interviewers",
      "stack": ["tech1", "tech2"],
      "difficulty": "beginner|intermediate|advanced"
    }}
  ],
  "mock_interview": [
    {{
      "question": "Interview question tailored to the resume and role",
      "sample_answer": "A strong sample answer the candidate can say in an interview (4-6 sentences). Use first person. Reference realistic experience from their profile when possible.",
      "explanation": "Detailed explanation (5-8 sentences): why this question is asked, key concepts to cover, common mistakes, and how interviewers evaluate the answer."
    }}
  ]
}}

Rules:
- Exactly 3 project_suggestions tailored to skill_gaps
- Exactly 10 mock_interview questions — no fewer
- Mix question types: technical fundamentals, projects on resume, problem-solving, behavioral, role-specific scenarios, and system/design basics where appropriate
- sample_answer and explanation must be detailed and educational, not one-liners
- Projects should be portfolio-ready for junior developers"""
