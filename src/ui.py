"""
ui.py
-----
Gradio interface for the Resume Architect.
"""

import os
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import gradio as gr
from src.ai_writer import generate_summary, suggest_jobs
from src.docx_builder import build_resume_docx
from src.pdf_builder import build_resume_pdf

CUSTOM_CSS = """
/* Global Font and Background */
body, .gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background-color: #f3f4f6 !important;
}

/* Hero Header */
#hero {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    color: #ffffff !important;
    padding: 30px; 
    border-radius: 12px; 
    margin-bottom: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    text-align: center;
}
#hero h1, #hero p, #hero span {
    color: #ffffff !important;
}
#hero h1 { margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }
#hero p { margin: 4px 0 0 0; opacity: 0.95; font-size: 15px; }

/* Cards */
.card {
    background: white !important; 
    border-radius: 12px !important; 
    padding: 24px !important; 
    box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06) !important;
    border: 1px solid #e5e7eb !important;
}

/* Input Fields (Making them look professional) */
.block {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}
label {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #374151 !important;
    margin-bottom: 4px !important;
}
input, textarea {
    border-radius: 8px !important;
    border: 1px solid #d1d5db !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    font-size: 14px !important;
    padding: 10px 12px !important;
}
input:focus, textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
}

/* Primary Button */
button.primary {
    background: #2563eb !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px !important;
    transition: background 0.2s !important;
}
button.primary:hover {
    background: #1d4ed8 !important;
}

/* Hide Gradio Footer */
footer { display: none !important; }
"""

def generate_resume(
    name,
    title,
    phone,
    email,
    location,
    education,
    experience,
    skills,
    communication,
    certificates,
    languages,
    job_jd_input,
):
    if not name or not email:
        return "⚠️ Please fill in at least your Name and Email.", "", None, None

    ai_summary = generate_summary(
        name,
        skills,
        experience,
        job_jd_input,
        certificates=certificates,
        communication=communication,
        languages=languages,
    )
    job_matches = suggest_jobs(
        title,
        skills,
        experience,
        education,
        certificates,
        communication,
        languages,
        job_jd_input,
    )
    data = {
        "name": name,
        "title": title,
        "phone": phone,
        "email": email,
        "location": location,
        "education": education,
        "experience": experience,
        "skills": skills,
        "communication": communication,
        "certificates": certificates,
        "languages": languages,
        "summary": ai_summary,
    }

    errors = []
    try:
        pdf_path = build_resume_pdf("modern.html", data)
    except Exception as exc:
        pdf_path = None
        errors.append(f"PDF: {exc}")
    try:
        docx_path = build_resume_docx(data)
    except Exception as exc:
        docx_path = None
        errors.append(f"Word: {exc}")

    if errors and not pdf_path and not docx_path:
        return "❌ " + " ".join(errors), job_matches, None, None
    if errors:
        status = "⚠️ Files are partly ready. " + " ".join(errors)
    else:
        status = "✅ PDF and Word are ready. Download either file and send it with your application."
    return status, job_matches, pdf_path, docx_path
def build_ui():
    with gr.Blocks(title="Resume Architect", css=CUSTOM_CSS) as demo:
        gr.HTML("""
        <div id="hero">
          <h1 style="color:#ffffff;">Resume Architect</h1>
          <p style="color:#ffffff;">Build a resume you can send today, as PDF or Word, plus jobs that fit your certificates.</p>
        </div>
        """)

        with gr.Column(elem_classes="card"):
            # Personal Details
            gr.Markdown("### 👤 Personal Details")
            with gr.Row():
                name_input = gr.Textbox(label="Full Name", placeholder="Sebastian Bennett")
                title_input = gr.Textbox(label="Professional Title", placeholder="Professional Accountant")
            with gr.Row():
                phone_input = gr.Textbox(label="Phone", placeholder="+123-456-7890")
                email_input = gr.Textbox(label="Email", placeholder="hello@reallygreatsite.com")
                location_input = gr.Textbox(label="Location", placeholder="123 Anywhere St.")

            gr.Markdown("### 🎓 Education")
            gr.Markdown(
                "One block per qualification. Line 1 is school | dates, line 2 is the qualification, then a short description. Leave a blank line between blocks."
            )
            education_input = gr.Textbox(
                label="Education",
                lines=8,
                placeholder=(
                    "Borcelle University | 2026-2030\n"
                    "Senior Accountant\n"
                    "Short description of what you studied.\n\n"
                    "Borcelle University | 2023-2026\n"
                    "Senior Accountant\n"
                    "Short description of what you studied."
                ),
            )

            gr.Markdown("### 💼 Work Experience")
            gr.Markdown(
                "One block per job. Line 1 is company | dates, line 2 is the job title, then a short description. Leave a blank line between jobs."
            )
            experience_input = gr.Textbox(
                label="Work Experience",
                lines=8,
                placeholder=(
                    "Salford & Co. | 2033 - 2035\n"
                    "Senior Accountant\n"
                    "Short description of what you did in this role.\n\n"
                    "Salford & Co. | 2030 - 2033\n"
                    "Financial Accountant\n"
                    "Short description of what you did in this role."
                ),
            )

            gr.Markdown("### ✦ Skills")
            skills_input = gr.Textbox(
                label="Skills (comma separated)",
                lines=2,
                placeholder="Auditing, Financial Accounting, Financial Reporting",
            )

            gr.Markdown("### 💬 Communication")
            communication_input = gr.Textbox(
                label="Communication skills (comma separated)",
                lines=2,
                placeholder="Client communication, Report writing, Presentations, Stakeholder updates",
            )

            gr.Markdown("### 📜 Certificates")
            gr.Markdown(
                "One block per certificate. Line 1 is the certificate | year, line 2 is who issued it, then a short line on what it covers. Leave a blank line between certificates."
            )
            certificates_input = gr.Textbox(
                label="Certificates",
                lines=6,
                placeholder=(
                    "CPA License | 2024\n"
                    "AICPA\n"
                    "Licensed to practice public accounting.\n\n"
                    "IFRS Certificate | 2023\n"
                    "ACCA\n"
                    "Certificate in international financial reporting."
                ),
            )

            gr.Markdown("### 🌐 Languages")
            languages_input = gr.Textbox(
                label="Languages",
                lines=3,
                placeholder="English | Native\nArabic | Professional\nFrench | Intermediate",
            )

            gr.Markdown("### 🎯 Target job")
            job_jd_input = gr.Textbox(
                label="Job description (optional)",
                lines=3,
                placeholder="Paste a job post here. The summary and the job matches will aim at that role.",
            )

            generate_btn = gr.Button("✨ Generate PDF and Word", variant="primary", size="lg")

        with gr.Column(elem_classes="card"):
            gr.Markdown("### 🎯 Jobs that fit your certificates")
            jobs_msg = gr.Markdown("*Generate a resume to see roles you can apply for.*")

        with gr.Column(elem_classes="card"):
            gr.Markdown("### 📥 Download")
            status_msg = gr.Markdown("*Fill out the form above and click Generate.*")
            with gr.Row():
                pdf_output = gr.File(label="PDF resume")
                docx_output = gr.File(label="Word resume")

        generate_btn.click(
            fn=generate_resume,
            inputs=[
                name_input, title_input, phone_input, email_input, location_input,
                education_input, experience_input, skills_input,
                communication_input, certificates_input, languages_input, job_jd_input
            ],
            outputs=[status_msg, jobs_msg, pdf_output, docx_output]
        )

    return demo

def launch_ui(share: bool = False):
    demo = build_ui()
    demo.launch(share=share, theme=gr.themes.Soft(), css=CUSTOM_CSS)
    return demo