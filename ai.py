import os
import json
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Preferred available models in order of preference
MODELS_TO_TRY = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b"
]

def analyze_resume(resume_text, user_goal):
    if not GROQ_API_KEY or not client:
        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "overall_feedback": "GROQ_API_KEY is not configured in the environment.",
            "error": "Missing Groq API Key"
        }

    prompt = f"""You are an elite career strategist, technical recruiter, and hiring manager.

Evaluate the candidate's resume thoroughly in relation to their target career goal.

Target Goal / Role:
"{user_goal}"

Candidate's Resume Text:
\"\"\"{resume_text}\"\"\"

Instructions:
1. Identify and extract all current skills directly relevant to the target role.
2. Identify missing skills, tools, knowledge areas, or certifications required for the target role.
3. Build a structured, actionable learning roadmap (step-by-step milestones) to bridge the skill gap.
4. Provide high-yield interview questions (both technical and situational/behavioral) tailored to this resume and target role.
5. Provide a concise overall evaluation and strategic advice.

Return your response strictly as valid JSON with the following structure:
{{
  "skills": ["skill 1", "skill 2", ...],
  "missing_skills": ["missing skill 1", "missing skill 2", ...],
  "roadmap": [
    {{"step": "Phase 1: Foundation", "description": "Details on what to learn/build", "duration": "2-4 Weeks"}},
    {{"step": "Phase 2: Advanced Topics", "description": "Details on advanced skills", "duration": "4-6 Weeks"}},
    {{"step": "Phase 3: Portfolio & Real-world Projects", "description": "Details on portfolio projects", "duration": "2-3 Weeks"}}
  ],
  "interview_questions": [
    {{"question": "Question text", "type": "Technical / Behavioral", "tip": "Brief advice on answering"}},
    ...
  ],
  "overall_feedback": "A thoughtful 2-3 sentence overview of their candidacy and biggest leverage points."
}}
"""

    last_error = None
    for model_name in MODELS_TO_TRY:
        try:
            response = client.chat.completions.create(
                model=model_name,
                temperature=0.3,
                max_tokens=2048,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional AI career coach. You only return strict, valid JSON responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )

            raw_content = response.choices[0].message.content.strip()
            
            # Clean possible markdown formatting
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            raw_content = raw_content.strip()

            parsed = json.loads(raw_content)
            
            # Ensure required keys exist
            return {
                "skills": parsed.get("skills") or parsed.get("Skills") or [],
                "missing_skills": parsed.get("missing_skills") or parsed.get("Missing Skills") or [],
                "roadmap": parsed.get("roadmap") or parsed.get("Roadmap") or [],
                "interview_questions": parsed.get("interview_questions") or parsed.get("Interview Questions") or [],
                "overall_feedback": parsed.get("overall_feedback") or parsed.get("Overall Feedback") or ""
            }

        except Exception as e:
            last_error = str(e)
            continue

    return {
        "skills": [],
        "missing_skills": [],
        "roadmap": [],
        "interview_questions": [],
        "overall_feedback": "Analysis failed due to API connectivity.",
        "error": f"Error analyzing resume: {last_error}"
    }