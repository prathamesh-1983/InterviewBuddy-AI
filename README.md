# 🤝 InterviewBuddy AI --- A Local AI Interview Partner for a Friend

*This is a submission for the [Hacktoberfest Weekend Challenge: Build
for a
Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## What I Built

I built **InterviewBuddy AI**, a beginner-friendly AI mock interview
partner for a friend who is preparing for **Data Analyst, Data
Executive, and MIS Executive interviews**.

The problem was simple: finding interview questions is easy, but finding
someone who is consistently available to conduct a realistic interview,
ask follow-up questions, and give useful feedback is much harder.

InterviewBuddy AI turns a resume into a personalized interview practice
session.

A user can:

-   Upload a resume in TXT, PDF, or DOCX format.
-   Select a target job role.
-   Choose an interview difficulty.
-   Generate personalized interview questions.
-   Answer questions in an interactive interview session.
-   Receive AI feedback on each answer.
-   See strengths, improvement areas, missing points, and suggestions.
-   Receive a final practice report and a short improvement plan.
-   Store interview-session information locally using SQLite.

The goal is not to replace a real interviewer. It is to give my friend
an always-available practice partner so they can practice repeatedly
without needing another person to be available every time.

## Demo

**Local demo:** Run the project locally using the instructions in the
GitHub README.

> For the final submission, include a short video showing: resume upload
> → role selection → AI-generated questions → answering → AI feedback →
> final report.

## Code

**GitHub repository:** (https://github.com/prathamesh-1983/InterviewBuddy-AI/tree/main)

``` text
interviewbuddy-ai/
│
├── backend/
│   ├── main.py
│   ├── ai.py
│   └── database.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── data/
├── uploads/
├── sample_resume.txt
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## How I Built It

InterviewBuddy AI is built around **open-source/open-weight AI running
locally** rather than depending on a closed hosted AI API.

### AI

The project uses:

-   **Gemma 3** as the open-weight language model.
-   **Ollama** for local model execution and inference.
-   **Python** for the AI and backend logic.

The basic AI flow is:

``` text
Resume
   ↓
Resume text extraction
   ↓
FastAPI backend
   ↓
Personalized prompt
   ↓
Ollama
   ↓
Gemma 3
   ↓
Interview questions
   ↓
Candidate answer
   ↓
Gemma 3 evaluation
   ↓
Feedback + score
   ↓
Final practice report
```

### Application Stack

``` text
Frontend
HTML + CSS + JavaScript
        │
        ▼
Backend
Python + FastAPI
        │
        ├──────────────► SQLite
        │
        ▼
Local AI
Ollama + Gemma 3
```

### Resume Processing

The application accepts:

-   `.txt`
-   `.pdf`
-   `.docx`

The extracted resume content is passed to the AI so that interview
questions can be relevant to the candidate's actual experience and
skills.

For example, a resume mentioning **Excel, Power BI, SQL, Python, and
data cleaning** can result in questions specifically related to those
skills instead of only generic interview questions.

### AI Interview Workflow

The AI is used for three major tasks:

1.  **Question generation** --- the model receives the candidate's
    resume, target role, and difficulty level and generates relevant
    interview questions.
2.  **Answer evaluation** --- after each answer, the model evaluates the
    response and identifies strengths, missing points, and areas for
    improvement.
3.  **Final report** --- after the interview, the model summarizes
    performance and creates a practical improvement plan.

## Why Does Open Innovation Matter?

Open innovation mattered for this project because the application is
intended to be a **personal, repeatable, and privacy-friendly interview
practice tool**.

Using a locally running open-weight model made several things possible.

### 1. The resume can stay local

A resume contains personal information such as education, work
experience, contact information, and skills.

With local inference, the core AI processing can happen on the user's
own computer instead of requiring every resume and interview answer to
be sent to a third-party hosted AI service.

``` text
Traditional hosted approach:

Resume → Internet → Closed AI API → Response


InterviewBuddy:

Resume → Local application → Local Gemma model → Response
```

### 2. No per-request AI API cost

A local model does not require a paid API request for every practice
question, making repeated interview practice more practical for students
and job seekers.

### 3. The AI layer is replaceable

Because the project communicates with Ollama, the model can be changed
without redesigning the entire application.

``` text
Gemma 3
   ↓
another compatible local model
```

### 4. More control over the AI

Running the model locally makes it easier to experiment with prompts,
model choices, response formats, and interview behavior without being
locked into one closed provider.

### 5. Open tools made the project accessible

The project uses technologies that a beginner can inspect, modify, and
learn from:

-   Python
-   FastAPI
-   HTML/CSS/JavaScript
-   SQLite
-   Ollama
-   Gemma 3

## My Agent Session

**DevRelay session:** `[Add your saved DevRelay session link here]`

This section can be updated with the saved DevRelay session so judges
can see the development process.

## What I Learned

Building InterviewBuddy AI helped me understand that a useful AI
application does not need to be extremely large.

The most important part was identifying a real problem for one person
and building around that problem.

I also learned how to:

-   Connect a web application to a local AI model.
-   Use an open-weight model through Ollama.
-   Build prompts around structured user information.
-   Extract information from uploaded resumes.
-   Create an AI evaluation workflow.
-   Store application data with SQLite.
-   Separate frontend, backend, database, and AI responsibilities.
-   Design an AI application around privacy and local inference.

## Future Improvements

If I continue developing InterviewBuddy AI, I would like to add:

-   Voice-based interviews.
-   Speech-to-text answers.
-   AI-generated follow-up questions.
-   Job-description upload and job-specific interviews.
-   Interview performance history and charts.
-   More detailed scoring for technical and behavioral questions.
-   Multilingual interview practice.
-   A recruiter/interviewer mode.
-   Better local model selection based on available hardware.
-   Optional deployment for friends who cannot run a local model.

## Prize Categories

Remove this section if no partner category applies.

Potential partner technologies used in the project:

-   **Ollama / local AI inference**
-   **Gemma 3 / open-weight AI**

If entering additional partner categories, list the applicable
categories according to the official challenge requirements.

------------------------------------------------------------------------

## Final Note

InterviewBuddy AI started with a simple question:

> **What could I build that would genuinely help a friend?**

The answer was not another generic chatbot.

It was a practice partner that could be available whenever they needed
it.

By combining a simple web application with a locally running open-weight
AI model, InterviewBuddy AI makes personalized interview practice more
accessible, repeatable, and privacy-friendly.

**Built for a friend. Built with open AI. Built to be useful.** 🤝
