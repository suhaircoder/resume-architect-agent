"""
ai_writer.py
------------
Uses Groq to generate a professional resume summary tailored to a specific Job Description.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


FALLBACK_SUMMARY = (
    "Experienced professional with a proven track record of delivering accurate, "
    "high-quality work. Combines technical skill with clear communication to support "
    "teams, clients, and business goals."
)


def _complete(prompt: str, system: str, fallback: str, max_tokens: int = 900) -> str:
    """Ask Groq for plain text. Always returns resume-safe wording if the call fails."""
    if not client:
        return fallback
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            model="openai/gpt-oss-20b",
            temperature=0.6,
            max_completion_tokens=max_tokens,
            reasoning_effort="low",
        )
        text = (chat_completion.choices[0].message.content or "").strip()
        return text or fallback
    except Exception:
        return fallback


def generate_summary(
    name: str,
    skills: str,
    experience: str,
    job_description: str,
    certificates: str = "",
    communication: str = "",
    languages: str = "",
) -> str:
    """Generate a professional summary tailored to the job description."""
    if not (job_description or "").strip():
        jd_context = "The candidate is looking for a general role in their field."
    else:
        jd_context = f"The candidate is applying for this specific job:\n{job_description[:1500]}"

    prompt = f"""You are an expert resume writer. Write a powerful, professional summary (3-4 sentences) for a candidate.

CANDIDATE INFO:
Name: {name}
Skills: {skills}
Communication skills: {communication}
Certificates: {certificates}
Languages: {languages}
Experience: {experience}

TARGET JOB CONTEXT:
{jd_context}

RULES:
- Write in first-person (implied, no "I").
- Do not use cliches like "passionate", "team player", or "hard worker".
- Mention the strongest certificate or credential when one is provided.
- Highlight the skills that match the target job context.
- Keep it under 80 words.
- Output ONLY the summary text. No quotes, no intro.
"""
    return _complete(prompt, "You are a professional resume writer.", FALLBACK_SUMMARY, 800)


def suggest_jobs(
    title: str,
    skills: str,
    experience: str,
    education: str,
    certificates: str,
    communication: str,
    languages: str,
    job_description: str = "",
) -> str:
    """Suggest real job titles that fit the person's certificates and background."""
    fallback = _fallback_jobs(title, skills, certificates)
    prompt = f"""You help people choose jobs they can apply for today.

CANDIDATE:
Current title: {title}
Certificates:
{certificates or "None listed"}
Skills: {skills or "None listed"}
Communication: {communication or "None listed"}
Languages: {languages or "None listed"}
Education:
{education or "None listed"}
Experience:
{experience or "None listed"}
Target notes: {(job_description or "None")[:800]}

Suggest exactly 5 job titles this person can apply for now.
Rank them by how well the certificates and skills fit.
For each job use this exact layout:

1. Job title
Why it fits: one sentence tied to a certificate, skill, or qualification.
Emphasize: two concrete words or duties to put on the application.

No introduction and no closing. Plain text only."""
    return _complete(
        prompt,
        "You are a practical career advisor. Recommend real, hireable job titles.",
        fallback,
        1000,
    )


def _fallback_jobs(title: str, skills: str, certificates: str) -> str:
    """Used when the model is unavailable. Still gives apply-ready titles."""
    blob = f"{title} {skills} {certificates}".lower()
    catalog = [
        (
            ["account", "audit", "cpa", "ifrs", "bookkeep", "finance", "tax"],
            [
                ("Senior Accountant", "accounting credentials and reporting experience"),
                ("Financial Accountant", "ledger, reporting, and close experience"),
                ("Auditor", "review and control work named in the certificates"),
                ("Accounts Supervisor", "a mix of technical accounting and communication"),
                ("Tax Associate", "formal finance or accounting qualifications"),
            ],
        ),
        (
            ["python", "developer", "software", "javascript", "data", "sql"],
            [
                ("Software Developer", "hands-on technical skills"),
                ("Backend Developer", "programming and data skills"),
                ("Data Analyst", "analysis skills that match the certificates"),
                ("Junior Software Engineer", "a path to apply while building experience"),
                ("Business Analyst", "technical skill plus communication"),
            ],
        ),
        (
            ["nurse", "clinic", "health", "care", "medical"],
            [
                ("Registered Nurse", "clinical certificates"),
                ("Clinic Coordinator", "care experience and communication"),
                ("Healthcare Assistant", "a direct way to use the certificates"),
                ("Patient Care Coordinator", "communication with patients and teams"),
                ("Medical Records Specialist", "accuracy and healthcare knowledge"),
            ],
        ),
    ]
    picks = None
    for words, jobs in catalog:
        if any(word in blob for word in words):
            picks = jobs
            break
    if picks is None:
        label = (title or "Professional").strip()
        picks = [
            (label, "the title already on this resume"),
            (f"{label} Specialist", "the certificates and daily skills"),
            (f"Junior {label}", "a way to apply while gaining more experience"),
            (f"{label} Assistant", "supporting work that still uses the qualifications"),
            (f"{label} Coordinator", "communication skills plus the technical background"),
        ]
    lines = []
    for index, (job, reason) in enumerate(picks, start=1):
        lines.append(f"{index}. {job}\nWhy it fits: {reason}.\nEmphasize: the matching certificate and the strongest skill.")
    return "\n\n".join(lines)