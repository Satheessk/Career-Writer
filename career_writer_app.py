import os
from io import BytesIO

import streamlit as st
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ==========================
# 1. OPENAI CLIENT
# ==========================

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_llm(prompt: str) -> str:
    """
    Calls OpenAI Chat Completion API and returns generated text.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",   # change if needed
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that writes professional emails and clean, ATS-friendly resumes."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR calling OpenAI API]\n{str(e)}"


# ==========================
# 2. PDF GENERATION FOR RESUME
# ==========================

def create_resume_pdf(resume_text: str) -> bytes:
    """
    Creates a simple PDF from resume_text and returns bytes.
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Basic settings
    x_margin = 40
    y_margin = 40
    max_width = width - 2 * x_margin

    # Start near top of page
    y = height - y_margin

    # Set font
    p.setFont("Helvetica", 11)

    # Draw text line by line, simple wrapping
    for line in resume_text.split("\n"):
        # Manual wrap if line is too long
        while len(line) > 0:
            # Estimate max characters per line (simple approximation)
            max_chars = 90
            to_draw = line[:max_chars]
            line = line[max_chars:]

            p.drawString(x_margin, y, to_draw)
            y -= 14  # line spacing

            # If we reach bottom, new page
            if y < y_margin:
                p.showPage()
                p.setFont("Helvetica", 11)
                y = height - y_margin

    p.showPage()
    p.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ==========================
# 3. STREAMLIT UI SETUP
# ==========================

st.set_page_config(page_title="CareerWriter - Email & Resume Generator", layout="centered")

st.title("✉️📄 CareerWriter - Email & Resume Auto Generator")
st.write("Generate **professional emails** and **clean resumes (with PDF download)** using OpenAI.")

tab_email, tab_resume = st.tabs(["📧 Email Generator", "📃 Resume Generator"])


# ==========================
# 4. EMAIL GENERATOR TAB
# ==========================
with tab_email:
    st.header("📧 Email Generator")

    email_type = st.selectbox(
        "Select Email Type",
        [
            "Internship request",
            "Job application",
            "Leave application",
            "College-related request (bonafide, fee receipt, etc.)",
            "Complaint / Issue",
            "Other"
        ]
    )

    receiver = st.text_input("Receiver (e.g., HOD, HR Manager, Warden)")
    tone = st.selectbox("Tone", ["Formal", "Semi-formal", "Friendly"])
    purpose = st.text_area("Purpose of the email (short description)")
    extra_details = st.text_area("Extra details (dates, reasons, skills, etc.)")

    email_text = ""
    if st.button("Generate Email"):
        if not receiver or not purpose:
            st.warning("Please fill at least the receiver and purpose.")
        else:
            email_prompt = f"""
You are an assistant that writes clear, professional emails.

Write an email with the following details:
- Type of email: {email_type}
- Receiver: {receiver}
- Tone: {tone}
- Purpose: {purpose}
- Extra details: {extra_details}

Requirements:
- Include a subject line.
- Use proper email format with greeting, body, and closing.
- Keep it concise and polite.
- Do NOT add explanations, just output the email.
"""
            with st.spinner("Generating email using OpenAI..."):
                email_text = call_llm(email_prompt)

            st.subheader("✉ Generated Email")
            st.text_area("Email Output", email_text, height=300)
            st.caption("You can copy-paste this into Gmail / Outlook / your college portal.")


# ==========================
# 5. RESUME GENERATOR TAB
# ==========================
with tab_resume:
    st.header("📃 Resume Generator")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        location = st.text_input("Location (City, Country)")

    with col2:
        summary = st.text_area("Career goal / summary (optional)", height=100)

    st.subheader("Education")
    education = st.text_area(
        "Education details (degree, college, year, CGPA). Example:\nB.Tech Information Technology, MIT, Anna University, 2027, CGPA: 8.5",
        height=100
    )

    st.subheader("Skills")
    skills = st.text_area(
        "List your skills (comma or line separated). Example:\nPython, C, Data Structures, HTML, CSS",
        height=80
    )

    st.subheader("Projects")
    projects = st.text_area(
        "Describe your projects (title + 1–2 lines each).",
        height=120
    )

    st.subheader("Experience / Internships (optional)")
    experience = st.text_area(
        "Internships, part-time work, volunteering (if any).",
        height=120
    )

    st.subheader("Achievements (optional)")
    achievements = st.text_area(
        "Scholarships, ranks, certifications, hackathons, etc.",
        height=100
    )

    resume_text = ""
    if st.button("Generate Resume"):
        if not name or not education or not skills:
            st.warning("Please fill at least Name, Education, and Skills.")
        else:
            resume_prompt = f"""
You are an assistant that writes clean, ATS-friendly resumes.

Create a resume in plain text using these details:

Name: {name}
Email: {email}
Phone: {phone}
Location: {location}

Career goal / summary (if any): {summary}

Education:
{education}

Skills:
{skills}

Projects:
{projects}

Experience / Internships:
{experience}

Achievements (if any):
{achievements}

Requirements:
- Use clear section headings: SUMMARY, EDUCATION, SKILLS, PROJECTS, EXPERIENCE, ACHIEVEMENTS.
- Use bullet points where needed.
- Make the language simple and strong.
- Do NOT invent fake details.
- Output only the resume text.
"""
            with st.spinner("Generating resume using OpenAI..."):
                resume_text = call_llm(resume_prompt)

            st.subheader("📄 Generated Resume")
            st.text_area("Resume Output", resume_text, height=400)

            # PDF download section (only if resume_text looks valid)
            if not resume_text.startswith("[ERROR"):
                pdf_bytes = create_resume_pdf(resume_text)
                st.download_button(
                    label="⬇ Download Resume as PDF",
                    data=pdf_bytes,
                    file_name=f"{name.replace(' ', '_')}_resume.pdf" if name else "resume.pdf",
                    mime="application/pdf"
                )
                st.caption("PDF is basic but good enough for project demo. You can improve styling later.")
            else:
                st.error("Could not generate PDF because there was an error from OpenAI.")
