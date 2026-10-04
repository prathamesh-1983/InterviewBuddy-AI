import json
import os
import re
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")


class OllamaError(RuntimeError):
    pass


def _extract_json(text: str) -> Any:
    """Extract JSON even when a model wraps it in markdown fences or extra text."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try the first object.
    start_obj = cleaned.find("{")
    end_obj = cleaned.rfind("}")
    if start_obj != -1 and end_obj > start_obj:
        try:
            return json.loads(cleaned[start_obj:end_obj + 1])
        except json.JSONDecodeError:
            pass

    # Try the first array.
    start_arr = cleaned.find("[")
    end_arr = cleaned.rfind("]")
    if start_arr != -1 and end_arr > start_arr:
        try:
            return json.loads(cleaned[start_arr:end_arr + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError("The AI returned a response that was not valid JSON.")


def ollama_chat(messages: list[dict[str, str]], temperature: float = 0.4) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=300,
        )
    except requests.RequestException as exc:
        raise OllamaError(
            "Cannot connect to Ollama. Start Ollama and make sure the selected "
            f"model '{OLLAMA_MODEL}' is installed."
        ) from exc

    if response.status_code != 200:
        raise OllamaError(
            f"Ollama returned HTTP {response.status_code}: {response.text[:500]}"
        )

    data = response.json()
    content = data.get("message", {}).get("content", "")
    if not content:
        raise OllamaError("Ollama returned an empty response.")
    return content


def generate_questions(
    resume: str,
    role: str,
    difficulty: str,
    count: int,
) -> dict:
    count = max(3, min(count, 10))

    system = """You are InterviewBuddy, a practical interview coach.
Create realistic interview questions for the requested job role.
Personalize questions using the candidate's resume.
Do not invent experience or skills that are not present.
Return ONLY valid JSON. No markdown. No explanation outside JSON."""

    user = f"""
Target role: {role}
Difficulty: {difficulty}
Number of questions: {count}

Candidate resume:
{resume[:12000]}

Return exactly this JSON shape:
{{
  "questions": [
    {{
      "id": 1,
      "type": "technical|behavioral|resume",
      "question": "question text",
      "why_it_matters": "short reason",
      "expected_points": ["point 1", "point 2", "point 3"]
    }}
  ]
}}

Rules:
- Include a useful mixture of technical, behavioral and resume-based questions.
- Keep questions suitable for a real entry-level or early-career interview.
- If the role is technical, include relevant technical concepts.
- Do not make up company-specific requirements.
- Keep each question concise.
"""

    raw = ollama_chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.5,
    )

    try:
        result = _extract_json(raw)
        if not isinstance(result, dict) or not result.get("questions"):
            raise ValueError("Missing questions.")
        return result
    except Exception:
        # A safe fallback keeps the demo usable if a small model produces malformed JSON.
        fallback = [
            {
                "id": 1,
                "type": "resume",
                "question": f"Walk me through the experience in your resume that is most relevant to the {role} role.",
                "why_it_matters": "Tests relevance, communication and resume ownership.",
                "expected_points": ["Specific example", "Your contribution", "Result or learning"],
            },
            {
                "id": 2,
                "type": "technical",
                "question": f"What are three important skills a {role} professional should have, and how have you practiced them?",
                "why_it_matters": "Tests role awareness and practical preparation.",
                "expected_points": ["Relevant skills", "Practical example", "Clear explanation"],
            },
            {
                "id": 3,
                "type": "behavioral",
                "question": "Tell me about a time you had to solve a difficult problem. What did you do?",
                "why_it_matters": "Tests structured problem solving.",
                "expected_points": ["Situation", "Action", "Result"],
            },
        ]
        return {"questions": fallback[:count]}


def evaluate_answer(
    role: str,
    question: str,
    answer: str,
    resume: str,
) -> dict:
    system = """You are a supportive but honest interview evaluator.
Evaluate an interview answer using the question and candidate context.
Return ONLY valid JSON. Do not make hiring decisions and do not claim to predict employment outcomes."""

    user = f"""
Target role: {role}

Question:
{question}

Candidate answer:
{answer}

Relevant resume:
{resume[:8000]}

Return exactly:
{{
  "score": 0,
  "verdict": "strong|good|developing|needs_work",
  "strengths": ["..."],
  "improvements": ["..."],
  "missing_points": ["..."],
  "better_answer_outline": ["..."],
  "follow_up_question": "..."
}}

Scoring:
0-39 = needs_work
40-59 = developing
60-79 = good
80-100 = strong

Be specific. Evaluate the answer, not the person.
"""

    raw = ollama_chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )

    try:
        result = _extract_json(raw)
        score = int(result.get("score", 0))
        result["score"] = max(0, min(100, score))
        return result
    except Exception:
        return {
            "score": 60,
            "verdict": "developing",
            "strengths": ["You attempted the question and provided a concrete response."],
            "improvements": ["Add a specific example and explain the result of your action."],
            "missing_points": ["A clearer structure would make the answer easier to follow."],
            "better_answer_outline": ["Situation", "Action", "Result", "Learning"],
            "follow_up_question": "What was the measurable result of the approach you described?",
        }


def generate_final_summary(
    role: str,
    evaluations: list[dict],
) -> dict:
    system = """You are an interview coach summarizing practice performance.
Return ONLY valid JSON. Do not make a hiring decision or predict employment."""

    user = f"""
Target role: {role}

Evaluations:
{json.dumps(evaluations, ensure_ascii=False)}

Return:
{{
  "overall_score": 0,
  "summary": "short paragraph",
  "top_strengths": ["..."],
  "top_improvements": ["..."],
  "practice_plan": [
    {{"day": "Day 1", "task": "..."}},
    {{"day": "Day 2", "task": "..."}},
    {{"day": "Day 3", "task": "..."}}
  ]
}}

The score should be an approximate practice score based only on the supplied evaluations.
"""

    raw = ollama_chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.35,
    )

    try:
        result = _extract_json(raw)
        result["overall_score"] = max(
            0, min(100, int(result.get("overall_score", 0)))
        )
        return result
    except Exception:
        scores = [int(x.get("score", 0)) for x in evaluations if x.get("score") is not None]
        avg = round(sum(scores) / len(scores)) if scores else 0
        return {
            "overall_score": avg,
            "summary": "Your practice session is complete. Use the feedback from each answer to improve clarity, specificity and role-relevant examples.",
            "top_strengths": ["You completed the practice session."],
            "top_improvements": ["Use specific examples and quantify outcomes where possible."],
            "practice_plan": [
                {"day": "Day 1", "task": "Review your weakest answer."},
                {"day": "Day 2", "task": "Practice two answers aloud using Situation, Action, Result."},
                {"day": "Day 3", "task": "Repeat the interview and compare your responses."},
            ],
        }


def health_check() -> dict:
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            return {"ollama": False, "model": OLLAMA_MODEL}
        models = [m.get("name", "") for m in response.json().get("models", [])]
        installed = OLLAMA_MODEL in models or any(
            m.split(":")[0] == OLLAMA_MODEL.split(":")[0] for m in models
        )
        return {"ollama": True, "model": OLLAMA_MODEL, "model_installed": installed}
    except requests.RequestException:
        return {"ollama": False, "model": OLLAMA_MODEL, "model_installed": False}
