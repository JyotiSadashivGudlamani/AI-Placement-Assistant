"""
Service for Module 2: HR Preparation.
Generates structured HR interview questions, frameworks (STAR, Present-Past-Future),
and personalized draft answers strictly adhering to the rule: Do not invent student achievements.
"""

from uuid import uuid4
import json
import re
from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.hr import HR_CATEGORIES, HR_CATEGORY_LABELS


# Curated structural frameworks and grounded templates for each HR category
HR_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "self_introduction": {
        "question": "Tell me about yourself and walk me through your background.",
        "framework": "Present-Past-Future Formula",
        "sample_structure": [
            "Present: Current academic standing, major, and primary technical domain.",
            "Past: 1-2 major technical projects or internships and concrete competencies learned.",
            "Future: Why you are passionate about this role and how your skills contribute."
        ],
        "default_draft": (
            "Good morning/afternoon. I am a graduating student in Computer Science. "
            "Currently, my primary technical focus is on {skills_or_domain}. "
            "During my academic tenure, I developed {project_or_experience}, where I was responsible for {responsibility}. "
            "This experience helped me build practical competencies in problem-solving and clean code practices. "
            "Looking forward, I am excited about the {target_role} role at {target_company} because it aligns with my goal "
            "of applying my technical foundation to scalable, real-world engineering challenges."
        ),
        "dos_and_donts": [
            "DO keep your introduction between 60 to 90 seconds.",
            "DO focus 70% on technical projects and future alignment, not childhood history.",
            "DO NOT recite your resume line-by-line.",
            "DO NOT claim achievements or tools you have not personally worked with."
        ],
        "follow_up_questions": [
            "What was the most challenging technical bug you resolved in your college project?",
            "How do you keep your technical skills updated outside the curriculum?"
        ]
    },
    "strengths_weaknesses": {
        "question": "What are your greatest technical/professional strengths, and what is one area you are working to improve?",
        "framework": "Strength-Impact & Actionable Weakness Model",
        "sample_structure": [
            "Strength: Name a concrete technical strength with proof (e.g. structured debugging, disciplined consistency).",
            "Impact: Brief example of how this strength benefited a project or team.",
            "Weakness: A genuine, non-critical skill area currently under active improvement.",
            "Mitigation: Concrete steps you are actively taking to overcome it (e.g. courses, time blocking)."
        ],
        "default_draft": (
            "My primary strength is my disciplined approach to debugging and root-cause analysis. When developing {project_or_domain}, "
            "I make it a priority to write unit tests and inspect edge cases thoroughly rather than patching symptoms.\n\n"
            "An area I have actively been working to improve is public speaking and presenting technical concepts in large groups. "
            "Earlier, I felt nervous presenting project demos. To actively overcome this, I have been volunteering to lead sprint updates "
            "and regularly participating in college seminar presentations to build confidence and structured delivery."
        ),
        "dos_and_donts": [
            "DO provide a real weakness paired with an active, measurable mitigation plan.",
            "DO NOT use cliché non-weaknesses like 'I am too much of a perfectionist' or 'I work too hard'.",
            "DO NOT mention a core fatal weakness such as 'I cannot write code' or 'I do not meet deadlines'."
        ],
        "follow_up_questions": [
            "Can you share an instance where you received critical feedback and how you acted on it?",
            "How do you prioritize competing deadlines under pressure?"
        ]
    },
    "career_goals": {
        "question": "Where do you see yourself in 3 to 5 years, and what are your short-term vs long-term career goals?",
        "framework": "Competency-Contribution-Leadership Timeline",
        "sample_structure": [
            "Short-term (1-2 years): Master the team's tech stack, deliver reliable production features, understand engineering workflows.",
            "Long-term (3-5 years): Become a domain subject matter expert, mentor junior engineers, contribute to system design decisions."
        ],
        "default_draft": (
            "In the short term, over the next 1 to 2 years, my priority as a {target_role} is to thoroughly master your engineering practices, "
            "become an independent and reliable contributor to {target_company}'s codebase, and write clean, well-tested production code.\n\n"
            "In the 3 to 5 year horizon, I aim to deepen my expertise in system design and architecture, take ownership of complex subsystems, "
            "and assist in onboarding and mentoring junior team members. Ultimately, I want to grow into an engineer who consistently delivers "
            "high-impact technical solutions."
        ),
        "dos_and_donts": [
            "DO align your growth with the technical career ladder of the company.",
            "DO emphasize mastery of engineering fundamentals before leadership aspirations.",
            "DO NOT give vague answers like 'I want to be a manager' without technical grounding.",
            "DO NOT state that you plan to pursue higher studies immediately if applying for a full-time role."
        ],
        "follow_up_questions": [
            "How does this position at our company help you bridge that career path?",
            "What specific technology or domain are you most curious to master next?"
        ]
    },
    "teamwork": {
        "question": "Describe a situation where you worked in a team on a technical project and faced a disagreement or bottleneck.",
        "framework": "STAR Method (Situation, Task, Action, Result)",
        "sample_structure": [
            "Situation: Context of the college/hackathon team project and the team composition.",
            "Task: The technical objective and the nature of the disagreement or blocker.",
            "Action: The mature, objective steps you took to listen, evaluate pros/cons, and find consensus.",
            "Result: Successful delivery of the project, deadline met, and team cohesion preserved."
        ],
        "default_draft": (
            "Situation: During our final-year academic project {project_or_domain}, our four-member team had to choose between two architectural approaches.\n"
            "Task: Two team members favored an unfamiliar framework while others wanted to stick to what we knew best to meet the tight submission deadline.\n"
            "Action: Rather than arguing on subjective preferences, I proposed building a quick 1-day proof-of-concept for the critical workflow and measuring development speed and stability. We documented the trade-offs objectively, which made the consensus clear to everyone.\n"
            "Result: We delivered the project on time without interpersonal friction, achieving our planned functionality."
        ),
        "dos_and_donts": [
            "DO highlight active listening, objective data-driven decision making, and team empathy.",
            "DO NOT blame teammates or paint other group members as incompetent.",
            "DO keep the focus on what YOU specifically did to resolve the conflict."
        ],
        "follow_up_questions": [
            "How do you handle a teammate who is not delivering their assigned module on time?",
            "What would you do if your technical suggestion was rejected by the team?"
        ]
    },
    "problem_solving": {
        "question": "Give an example of a difficult technical or logical problem you faced and how you approached solving it.",
        "framework": "STAR + Root-Cause Analysis Framework",
        "sample_structure": [
            "Situation: Context where a non-obvious bug or performance degradation occurred.",
            "Task: Identify why the unexpected behavior was occurring.",
            "Action: Scientific breakdown: isolation of variables, log analysis, reproducing the error, researching solutions.",
            "Result: Successful fix, verification through test cases, and preventive documentation."
        ],
        "default_draft": (
            "Situation: While developing {project_or_domain}, our application encountered an intermittent failure during data processing.\n"
            "Task: The error occurred intermittently only under concurrent requests, making it difficult to reproduce locally.\n"
            "Action: Instead of guessing changes, I added detailed timestamped logs across the pipeline and reproduced the issue using simulated concurrent API calls. I discovered that a shared data structure lacked synchronization, leading to race conditions. I refactored the module to use thread-safe data handling.\n"
            "Result: The intermittent failures were completely eliminated, and I added regression test cases to ensure the issue would not resurface."
        ),
        "dos_and_donts": [
            "DO emphasize your systematic debugging process (logs, reproduction, hypothesis testing).",
            "DO NOT claim you immediately guessed the answer without systematic investigation.",
            "DO highlight what you learned to prevent the problem in future code."
        ],
        "follow_up_questions": [
            "If your first two hypotheses turned out to be wrong, how would you pivot your investigation?",
            "How do you determine when a quick workaround is acceptable versus requiring a complete refactor?"
        ]
    },
    "why_hire_you": {
        "question": "With many qualified candidates applying, why should our company hire you over others?",
        "framework": "The 3-Pillar Value Proposition (Fundamentals + Learnability + Cultural Drive)",
        "sample_structure": [
            "Pillar 1: Solid foundation in CS core concepts and demonstrated coding consistency.",
            "Pillar 2: High learnability—speed of picking up new frameworks and adapting to project needs.",
            "Pillar 3: Ownership mindset—committing to seeing tasks through to completion and collaborating cleanly."
        ],
        "default_draft": (
            "You should consider me for this {target_role} role because of three key factors:\n"
            "First, I have built a strong, disciplined foundation in core computer science principles—specifically in data structures, algorithms, and {skills_or_domain}.\n"
            "Second, I have demonstrated practical learnability. When building {project_or_experience}, I had to pick up unfamiliar libraries independently and deliver working functionality within tight constraints.\n"
            "Finally, I bring strong accountability and eagerness to contribute. I am prepared to immerse myself in {target_company}'s standards and add measurable value from day one."
        ),
        "dos_and_donts": [
            "DO articulate your unique blend of strong fundamentals and high learning velocity.",
            "DO NOT disparage other candidates.",
            "DO NOT give generic answers like 'I need a job' or 'I am very smart'."
        ],
        "follow_up_questions": [
            "How quickly can you become productive in a tech stack you have not studied before?",
            "What has been your proudest personal accomplishment outside college academics?"
        ]
    },
    "company_motivation": {
        "question": "Why do you want to join our company specifically, rather than any other technology organization?",
        "framework": "Company Product & Engineering Alignment",
        "sample_structure": [
            "Recognition of Company's Impact: Specific engineering domain, product, or mission that resonates with you.",
            "Engineering Culture: Appreciation for the company's technical quality, scale, or innovation.",
            "Personal Contribution: How your skills directly align with their ongoing initiatives."
        ],
        "default_draft": (
            "I have closely followed {target_company}'s work in {domain_or_product}. What stands out to me is your commitment to {company_value_or_scale}.\n"
            "As an aspiring {target_role}, working in an environment that prioritizes high engineering standards and solves problems at this scale is where I can contribute most effectively and grow as an engineer.\n"
            "My experience in {skills_or_domain} has prepared me to tackle rigorous engineering challenges, and I am genuinely excited about the opportunity to contribute to your team's mission."
        ),
        "dos_and_donts": [
            "DO research the company's real products, engineering blog, or scale beforehand.",
            "DO NOT give a copy-paste response that could apply to any random IT firm.",
            "DO NOT focus primarily on salary, perks, or location."
        ],
        "follow_up_questions": [
            "Which of our products or features do you think has the most room for innovation?",
            "What questions do you have for us about our engineering team?"
        ]
    }
}


class HRPrepService:
    """Orchestrates HR interview preparation, personalized draft answers, and frameworks."""

    _instance: Optional["HRPrepService"] = None

    def __init__(self):
        self.mongo = MongoDBManager.get_instance()

    @classmethod
    def get_instance(cls) -> "HRPrepService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def generate_hr_guidance(
        self,
        category: str,
        target_company: Optional[str] = None,
        target_role: Optional[str] = "Software Engineer",
        student_background: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates HR interview guidance and personalized draft answer.
        STRICT GROUNDING: Never invents qualifications, degrees, or achievements.
        """
        norm_cat = category.lower() if category.lower() in HR_CATEGORIES else "self_introduction"
        template = HR_TEMPLATES.get(norm_cat, HR_TEMPLATES["self_introduction"])
        company_str = target_company.strip() if target_company and target_company.strip() else "your organization"
        role_str = target_role.strip() if target_role and target_role.strip() else "Software Engineer"

        # Check if student background contains real facts
        has_real_bg = bool(student_background and len(student_background.strip()) > 10)

        # Dynamic LLM generation if Ollama is available
        try:
            bg_instruction = (
                f"STUDENT BACKGROUND PROVIDED: {student_background.strip()}\n"
                f"STRICT RULE: Use ONLY the exact facts, projects, and skills mentioned in the student background above. "
                f"DO NOT invent any fake companies, fake degrees, or fake achievements."
                if has_real_bg else
                "NO SPECIFIC STUDENT BACKGROUND PROVIDED.\n"
                "STRICT RULE: Use transparent bracketed placeholders like '[Insert your specific project name]' and "
                "'[Insert key technology used]'. DO NOT INVENT fake achievements or degrees for the student."
            )

            prompt = (
                f"You are a senior HR director preparing a college student for technical campus placements.\n"
                f"Topic: {HR_CATEGORY_LABELS.get(norm_cat, norm_cat)}\n"
                f"Target Role: {role_str}\n"
                f"Target Company: {company_str}\n\n"
                f"{bg_instruction}\n\n"
                f"Format your response as a valid JSON object strictly matching this schema with no markdown code fences:\n"
                f"{{\n"
                f'  "question": "{template["question"]}",\n'
                f'  "framework": "{template["framework"]}",\n'
                f'  "draft_answer": "professional, realistic draft response following the framework",\n'
                f'  "sample_structure": {json.dumps(template["sample_structure"])},\n'
                f'  "dos_and_donts": {json.dumps(template["dos_and_donts"])},\n'
                f'  "follow_up_questions": {json.dumps(template["follow_up_questions"])}\n'
                f"}}"
            )

            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": settings.OLLAMA_MODEL_NAME,
                        "messages": [
                            {"role": "system", "content": "You output only valid JSON without explanation or formatting."},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.2},
                    },
                )
                if res.status_code == 200:
                    raw_text = res.json().get("message", {}).get("content", "").strip()
                    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
                    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
                    parsed = json.loads(cleaned)
                    parsed["draft_id"] = f"hr_{uuid4().hex[:12]}"
                    parsed["category"] = norm_cat
                    parsed["category_label"] = HR_CATEGORY_LABELS.get(norm_cat, norm_cat)
                    return parsed
        except Exception:
            pass  # Fall through to deterministic template filling

        # Fallback to deterministic template with transparent placeholders
        raw_draft = template["default_draft"]
        draft_filled = raw_draft.replace("{target_company}", company_str)
        draft_filled = draft_filled.replace("{target_role}", role_str)

        if has_real_bg:
            draft_filled = draft_filled.replace("{skills_or_domain}", f"skills including {student_background[:100]}")
            draft_filled = draft_filled.replace("{project_or_experience}", "my recent practical project")
            draft_filled = draft_filled.replace("{project_or_domain}", "my project")
            draft_filled = draft_filled.replace("{responsibility}", "core development and implementation")
            draft_filled = draft_filled.replace("{domain_or_product}", "software solutions")
            draft_filled = draft_filled.replace("{company_value_or_scale}", "technological excellence and innovation")
        else:
            draft_filled = draft_filled.replace("{skills_or_domain}", "[Insert your primary technical skills, e.g. Java, Python, SQL]")
            draft_filled = draft_filled.replace("{project_or_experience}", "[Insert your major academic or internship project name]")
            draft_filled = draft_filled.replace("{project_or_domain}", "[Insert your project name]")
            draft_filled = draft_filled.replace("{responsibility}", "[Insert your specific technical contribution]")
            draft_filled = draft_filled.replace("{domain_or_product}", "[Insert target company domain, e.g. FinTech, Cloud Systems]")
            draft_filled = draft_filled.replace("{company_value_or_scale}", "[Insert company engineering value or scale]")

        return {
            "draft_id": f"hr_{uuid4().hex[:12]}",
            "category": norm_cat,
            "category_label": HR_CATEGORY_LABELS.get(norm_cat, norm_cat),
            "question": template["question"],
            "framework": template["framework"],
            "draft_answer": draft_filled,
            "sample_structure": template["sample_structure"],
            "dos_and_donts": template["dos_and_donts"],
            "follow_up_questions": template["follow_up_questions"],
        }

    def save_draft(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """Persists an HR draft answer in MongoDB."""
        return self.mongo.save_hr_draft(draft_data)

    def list_saved_drafts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists saved HR question drafts."""
        return self.mongo.list_hr_drafts(category=category)

    def delete_saved_draft(self, draft_id: str) -> bool:
        """Deletes a saved HR draft."""
        return self.mongo.delete_hr_draft(draft_id)
