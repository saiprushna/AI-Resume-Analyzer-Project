const form = document.getElementById("analyzeForm");
const fileInput = document.getElementById("resumeFile");
const dropZone = document.getElementById("dropZone");
const dropHint = document.getElementById("dropHint");
const fileNameBlock = document.getElementById("fileName");
const fileNameText = document.getElementById("fileNameText");
const clearFileBtn = document.getElementById("clearFile");
const submitBtn = document.getElementById("submitBtn");
const roleSelect = document.getElementById("targetRole");
const healthStatus = document.getElementById("healthStatus");

const loadingSection = document.getElementById("loadingSection");
const errorSection = document.getElementById("errorSection");
const errorText = document.getElementById("errorText");
const resultsSection = document.getElementById("resultsSection");

const RING_CIRCUMFERENCE = 326;

function show(el) {
  el.classList.remove("hidden");
}

function hide(el) {
  el.classList.add("hidden");
}

function setHealth(ok, label) {
  healthStatus.textContent = label;
  healthStatus.className = "status-pill " + (ok ? "status-pill--ok" : "status-pill--warn");
}

async function loadRoles() {
  const response = await fetch("/api/roles");
  const data = await response.json();
  roleSelect.innerHTML = "";

  const groups = data.groups || [];
  if (groups.length > 0) {
    for (const group of groups) {
      const optgroup = document.createElement("optgroup");
      optgroup.label = group.label;
      for (const role of group.roles || []) {
        const option = document.createElement("option");
        option.value = role;
        option.textContent = role;
        optgroup.appendChild(option);
      }
      roleSelect.appendChild(optgroup);
    }
    return;
  }

  for (const role of data.roles || []) {
    const option = document.createElement("option");
    option.value = role;
    option.textContent = role;
    roleSelect.appendChild(option);
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    setHealth(data.status === "ok", data.llm || data.status);
  } catch {
    setHealth(false, "Server offline");
  }
}

function setSelectedFile(file) {
  if (!file) return;
  fileInput.files = createFileList(file);
  hide(dropHint);
  fileNameText.textContent = file.name;
  show(fileNameBlock);
  dropZone.classList.add("drop-zone--filled");
}

function clearFile() {
  fileInput.value = "";
  show(dropHint);
  hide(fileNameBlock);
  dropZone.classList.remove("drop-zone--filled");
}

function createFileList(file) {
  const dt = new DataTransfer();
  dt.items.add(file);
  return dt.files;
}

dropZone.addEventListener("click", (event) => {
  if (event.target.closest("#clearFile")) return;
  fileInput.click();
});

clearFileBtn.addEventListener("click", (event) => {
  event.stopPropagation();
  clearFile();
});

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragover");
  const file = event.dataTransfer.files[0];
  if (file) setSelectedFile(file);
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) setSelectedFile(file);
});

function renderTags(container, items, emptyText) {
  container.innerHTML = "";
  if (!items || items.length === 0) {
    container.innerHTML = `<span class="empty">${emptyText}</span>`;
    return;
  }
  for (const item of items) {
    const span = document.createElement("span");
    span.className = "tag";
    span.textContent = item;
    container.appendChild(span);
  }
}

function scoreTier(score) {
  if (score < 50) return "score-low";
  if (score < 75) return "score-mid";
  return "score-high";
}

function scoreLabelText(score) {
  if (score < 50) return "Needs improvement — focus on closing skill gaps";
  if (score < 75) return "Good foundation — polish and add impact metrics";
  return "Strong resume — ready for interviews";
}

function setAtsScore(score) {
  const tier = scoreTier(score);
  const progress = document.getElementById("scoreRingProgress");
  const label = document.getElementById("scoreLabel");

  document.getElementById("atsScore").textContent = score;
  progress.classList.remove("score-low", "score-mid", "score-high");
  progress.classList.add(tier);

  label.className = "score-label " + tier;
  label.textContent = scoreLabelText(score);

  const offset = RING_CIRCUMFERENCE - (score / 100) * RING_CIRCUMFERENCE;
  requestAnimationFrame(() => {
    progress.style.strokeDashoffset = String(offset);
  });
}

function renderResults(data) {
  setAtsScore(data.ats_score);
  document.getElementById("candidateName").textContent = data.candidate_name || "Candidate";
  document.getElementById("targetRoleLabel").textContent = data.target_role;
  document.getElementById("feedbackText").textContent =
    data.ats_feedback || "No feedback available.";

  renderTags(document.getElementById("skillsFound"), data.skills_found, "No skills detected");
  renderTags(document.getElementById("skillGaps"), data.skill_gaps, "No major gaps");

  const strengthsList = document.getElementById("strengthsList");
  strengthsList.innerHTML = "";
  for (const item of data.strengths || []) {
    const li = document.createElement("li");
    li.textContent = item;
    strengthsList.appendChild(li);
  }

  const projectCards = document.getElementById("projectCards");
  projectCards.innerHTML = "";
  for (const project of data.project_suggestions || []) {
    const card = document.createElement("article");
    card.className = "project-card";
    const diffClass =
      "difficulty difficulty--" + (project.difficulty || "intermediate").toLowerCase();
    const stackHtml = (project.stack || [])
      .map((tech) => `<span class="stack-chip">${tech}</span>`)
      .join("");
    card.innerHTML =
      `<div class="project-card__head">` +
      `<h3>${project.title}</h3>` +
      `<span class="${diffClass}">${project.difficulty || "intermediate"}</span>` +
      `</div>` +
      `<p>${project.why}</p>` +
      `<div class="project-card__stack">${stackHtml}</div>`;
    projectCards.appendChild(card);
  }

  const questions = data.mock_interview || [];
  document.getElementById("interviewCount").textContent =
    `${questions.length} question${questions.length === 1 ? "" : "s"}`;

  const interviewList = document.getElementById("interviewList");
  interviewList.innerHTML = "";
  questions.forEach((item, index) => {
    const question = item.question || "Interview question";
    const answer = item.sample_answer || "";
    const explanation = item.explanation || "";

    const details = document.createElement("details");
    details.className = "interview-item";
    if (index === 0) details.open = true;
    details.innerHTML =
      `<summary><span class="interview-item__num">${index + 1}</span>${question}</summary>` +
      `<div class="interview-body">` +
      `<div class="interview-section">` +
      `<p class="interview-section__label">Sample answer</p>` +
      `<p>${answer}</p>` +
      `</div>` +
      `<div class="interview-section interview-section--explain">` +
      `<p class="interview-section__label">Detailed explanation</p>` +
      `<p>${explanation}</p>` +
      `</div>` +
      `</div>`;
    interviewList.appendChild(details);
  });

  show(resultsSection);
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hide(errorSection);
  hide(resultsSection);

  const file = fileInput.files[0];
  if (!file) {
    errorText.textContent = "Please select a resume PDF or DOCX file.";
    show(errorSection);
    return;
  }

  const body = new FormData();
  body.append("file", file);
  body.append("target_role", roleSelect.value);

  submitBtn.disabled = true;
  show(loadingSection);

  try {
    const response = await fetch("/api/analyze", { method: "POST", body });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Analysis failed");
    }
    renderResults(data);
  } catch (error) {
    errorText.textContent = error.message || "Something went wrong";
    show(errorSection);
  } finally {
    hide(loadingSection);
    submitBtn.disabled = false;
  }
});

loadRoles();
checkHealth();
