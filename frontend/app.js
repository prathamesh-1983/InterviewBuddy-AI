const state = {
  resumeText: "",
  resumeName: "Pasted resume",
  role: "Data Analyst",
  difficulty: "Intermediate",
  sessionId: null,
  questions: [],
  evaluations: [],
  currentIndex: 0,
};

const $ = (id) => document.getElementById(id);

function show(viewId) {
  ["setupView", "interviewView", "resultsView"].forEach((id) => {
    $(id).classList.toggle("hidden", id !== viewId);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showLoading(title = "Gemma is thinking...", message = "Local AI can take a little longer on a CPU.") {
  $("loadingTitle").textContent = title;
  $("loadingMessage").textContent = message;
  $("loadingOverlay").classList.remove("hidden");
}

function hideLoading() {
  $("loadingOverlay").classList.add("hidden");
}

function showError(message) {
  const box = $("errorBox");
  box.textContent = message;
  box.classList.remove("hidden");
  box.scrollIntoView({ behavior: "smooth", block: "center" });
}

function clearError() {
  $("errorBox").classList.add("hidden");
  $("errorBox").textContent = "";
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }
  if (!response.ok) {
    throw new Error(data.detail || `Request failed with HTTP ${response.status}`);
  }
  return data;
}

async function checkHealth() {
  try {
    const data = await api("/api/health");
    const dot = document.querySelector(".status-dot");
    $("statusText").textContent = data.model_installed
      ? `AI ready • ${data.model}`
      : `Ollama ready • install ${data.model}`;
    dot.style.background = data.model_installed ? "var(--accent-2)" : "#ffbd69";
  } catch {
    $("statusText").textContent = "Ollama not detected";
    document.querySelector(".status-dot").style.background = "var(--danger)";
  }
}

$("resumeFile").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  $("fileStatus").textContent = `Reading ${file.name}...`;
  clearError();

  const formData = new FormData();
  formData.append("file", file);

  try {
    const data = await api("/api/resume/extract", {
      method: "POST",
      body: formData,
    });

    state.resumeText = data.text;
    state.resumeName = data.filename;
    $("resumeText").value = data.text;
    $("fileStatus").textContent = `✓ ${data.filename} • ${data.characters} characters`;
  } catch (error) {
    $("fileStatus").textContent = "Could not read the file.";
    showError(error.message);
  }
});

$("resumeText").addEventListener("input", () => {
  state.resumeText = $("resumeText").value;
  state.resumeName = "Pasted resume";
});

$("startButton").addEventListener("click", async () => {
  clearError();

  state.resumeText = $("resumeText").value.trim();
  state.role = $("role").value.trim();
  state.difficulty = $("difficulty").value;

  if (state.resumeText.length < 30) {
    showError("Please upload a resume or paste at least a short profile.");
    return;
  }

  if (state.role.length < 2) {
    showError("Please enter a target job role.");
    return;
  }

  showLoading("Building your interview...", "Gemma is creating questions from the candidate profile.");

  try {
    const data = await api("/api/interview/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role: state.role,
        difficulty: state.difficulty,
        question_count: Number($("questionCount").value),
        resume_text: state.resumeText,
        resume_name: state.resumeName,
      }),
    });

    state.sessionId = data.session_id;
    state.questions = data.questions;
    state.evaluations = [];
    state.currentIndex = 0;

    $("interviewRole").textContent = `${state.role} Interview`;
    show("interviewView");
    renderQuestion();
  } catch (error) {
    showError(error.message);
  } finally {
    hideLoading();
  }
});

function renderQuestion() {
  const q = state.questions[state.currentIndex];
  const total = state.questions.length;
  const current = state.currentIndex + 1;
  const percent = Math.round((current / total) * 100);

  $("progressText").textContent = `Question ${current} of ${total}`;
  $("progressPercent").textContent = `${percent}%`;
  $("progressFill").style.width = `${percent}%`;

  $("questionType").textContent = (q.type || "INTERVIEW").toUpperCase();
  $("questionNumber").textContent = `Q${current}`;
  $("questionText").textContent = q.question;
  $("whyText").textContent = q.why_it_matters || "";
  $("answerText").value = "";
  $("feedbackPanel").classList.add("hidden");
  $("submitAnswerButton").classList.remove("hidden");
  $("answerText").disabled = false;

  $("coachMessage").textContent =
    current === 1
      ? "Start with a clear structure. Think about the example you want to use before answering."
      : "Focus on what you personally did, why you did it, and what happened next.";
}

$("submitAnswerButton").addEventListener("click", async () => {
  const answer = $("answerText").value.trim();

  if (answer.length < 2) {
    $("answerText").focus();
    return;
  }

  const q = state.questions[state.currentIndex];

  showLoading("Evaluating your answer...", "Gemma is looking at strengths, missing points and ways to improve.");

  try {
    const result = await api("/api/interview/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        role: state.role,
        question: q.question,
        answer,
        resume_text: state.resumeText,
      }),
    });

    state.evaluations.push(result);
    renderFeedback(result);
  } catch (error) {
    showError(error.message);
  } finally {
    hideLoading();
  }
});

function fillList(elementId, items) {
  const el = $(elementId);
  el.innerHTML = "";
  (items || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  });
}

function renderFeedback(result) {
  $("feedbackPanel").classList.remove("hidden");
  $("feedbackVerdict").textContent = titleCase(result.verdict || "Feedback");
  $("scoreCircle").textContent = result.score ?? "--";

  fillList("strengthsList", result.strengths);
  fillList("improvementsList", result.improvements);
  fillList("missingList", result.missing_points);
  fillList("outlineList", result.better_answer_outline);

  const isLast = state.currentIndex === state.questions.length - 1;
  $("nextButton").textContent = isLast ? "Finish interview →" : "Next question →";
  $("answerText").disabled = true;
  $("submitAnswerButton").classList.add("hidden");

  $("feedbackPanel").scrollIntoView({ behavior: "smooth", block: "start" });
}

$("nextButton").addEventListener("click", async () => {
  if (state.currentIndex < state.questions.length - 1) {
    state.currentIndex += 1;
    renderQuestion();
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }

  await finishInterview();
});

async function finishInterview() {
  showLoading("Creating your practice report...", "Gemma is turning the answer feedback into a short improvement plan.");

  try {
    const result = await api("/api/interview/final", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        role: state.role,
        evaluations: state.evaluations,
      }),
    });

    renderResults(result);
    show("resultsView");
  } catch (error) {
    showError(error.message);
  } finally {
    hideLoading();
  }
}

function renderResults(result) {
  $("overallScore").textContent = result.overall_score ?? "--";
  $("summaryTitle").textContent =
    result.overall_score >= 80
      ? "Strong practice session."
      : result.overall_score >= 60
        ? "Good foundation. Keep sharpening it."
        : "A useful starting point for practice.";
  $("summaryText").textContent = result.summary || "";

  fillList("topStrengths", result.top_strengths);
  fillList("topImprovements", result.top_improvements);

  const plan = $("practicePlan");
  plan.innerHTML = "";
  (result.practice_plan || []).forEach((item) => {
    const div = document.createElement("div");
    div.className = "practice-item";
    div.innerHTML = `<strong>${escapeHtml(item.day)}</strong><span>${escapeHtml(item.task)}</span>`;
    plan.appendChild(div);
  });
}

$("newInterviewButton").addEventListener("click", () => {
  state.sessionId = null;
  state.questions = [];
  state.evaluations = [];
  state.currentIndex = 0;
  $("sessionsPanel").classList.add("hidden");
  show("setupView");
});

$("quitButton").addEventListener("click", () => {
  if (confirm("Exit this interview session? Unsaved browser state will be cleared.")) {
    show("setupView");
  }
});

$("viewSessionsButton").addEventListener("click", async () => {
  const panel = $("sessionsPanel");
  panel.classList.toggle("hidden");
  if (panel.classList.contains("hidden")) return;

  try {
    const data = await api("/api/sessions");
    const list = $("sessionsList");
    list.innerHTML = "";

    if (!data.sessions.length) {
      list.textContent = "No saved sessions yet.";
      return;
    }

    data.sessions.forEach((session) => {
      const div = document.createElement("div");
      div.className = "practice-item";
      div.innerHTML = `
        <strong>Session #${session.id} — ${escapeHtml(session.role)}</strong>
        <span>${escapeHtml(session.difficulty)} • ${escapeHtml(session.resume_name || "Resume")} • ${escapeHtml(session.created_at)}</span>
      `;
      list.appendChild(div);
    });
  } catch (error) {
    showError(error.message);
  }
});

function titleCase(value) {
  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

checkHealth();
