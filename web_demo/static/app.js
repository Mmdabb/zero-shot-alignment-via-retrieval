const examples = {
  formal: {
    prompt: "Write a professional email asking a professor for a meeting.",
    response: ""
  },
  technical: {
    prompt: "Explain gradient descent in a technical way.",
    response: ""
  },
  casual: {
    prompt: "Tell me casually what this project does.",
    response: ""
  },
  friendly: {
    prompt: "Explain machine learning like a supportive friend.",
    response: ""
  }
};

const promptEl = document.getElementById("prompt");
const responseEl = document.getElementById("response");
const runBtn = document.getElementById("runBtn");
const bestStyleEl = document.getElementById("bestStyle");
const baseProviderEl = document.getElementById("baseProvider");
const alignmentProviderEl = document.getElementById("alignmentProvider");
const baseSourceEl = document.getElementById("baseSource");
const retrievalModelEl = document.getElementById("retrievalModel");
const scoresEl = document.getElementById("scores");
const baseResponseEl = document.getElementById("baseResponse");
const styledResponseEl = document.getElementById("styledResponse");
const augmentationEl = document.getElementById("augmentation");
const providerAttemptsEl = document.getElementById("providerAttempts");
const logFileEl = document.getElementById("logFile");

document.querySelectorAll("[data-example]").forEach(btn => {
  btn.addEventListener("click", () => {
    const ex = examples[btn.dataset.example];
    promptEl.value = ex.prompt;
    responseEl.value = ex.response;
  });
});

runBtn.addEventListener("click", runAlignment);

function normalizeScore(score, minScore, maxScore) {
  const range = maxScore - minScore || 1;
  return ((score - minScore) / range) * 100;
}

function renderScores(topStyles) {
  scoresEl.innerHTML = "";

  if (!topStyles || topStyles.length === 0) {
    scoresEl.innerHTML = "<p>No scores returned.</p>";
    return;
  }

  const scores = topStyles.map(item => item[1]);
  const minScore = Math.min(...scores);
  const maxScore = Math.max(...scores);

  topStyles.forEach(([name, score]) => {
    const pct = Math.max(normalizeScore(score, minScore, maxScore), 6);
    const row = document.createElement("div");
    row.className = "score-row";
    row.innerHTML = `
      <div class="score-head">
        <strong>${name}</strong>
        <span>${Number(score).toFixed(4)}</span>
      </div>
      <div class="bar-bg">
        <div class="bar" style="width:${pct}%"></div>
      </div>
    `;
    scoresEl.appendChild(row);
  });
}

function renderProviderAttempts(attempts) {
  if (!attempts || attempts.length === 0) {
    providerAttemptsEl.textContent = "manual base response -> alignment pending";
    return;
  }

  providerAttemptsEl.innerHTML = "";
  attempts.forEach((attempt, index) => {
    const item = document.createElement("span");
    item.className = attempt.success ? "attempt success" : "attempt failure";
    item.textContent = `${attempt.provider} ${attempt.success ? "succeeded" : "failed"}`;
    providerAttemptsEl.appendChild(item);

    if (index < attempts.length - 1) {
      const arrow = document.createElement("span");
      arrow.className = "attempt-arrow";
      arrow.textContent = "->";
      providerAttemptsEl.appendChild(arrow);
    }
  });
}

async function runAlignment() {
  const prompt = promptEl.value.trim();
  const response = responseEl.value.trim();

  if (!prompt) {
    alert("Please enter a user query.");
    return;
  }

  runBtn.disabled = true;
  runBtn.textContent = "Running alignment...";
  baseResponseEl.textContent = "Generating before-alignment response...";
  styledResponseEl.textContent = "Generating after-alignment response...";

  try {
    const body = response ? { prompt, response } : { prompt };
    const res = await fetch("/align", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.details || data.error || "Unknown backend error");
    }

    bestStyleEl.textContent = data.best_style;
    baseProviderEl.textContent = `${data.base_provider} / ${data.base_model}`;
    alignmentProviderEl.textContent = `${data.alignment_provider} / ${data.alignment_model}`;
    baseSourceEl.textContent = data.base_response_source;
    retrievalModelEl.textContent = data.retrieval_model;
    baseResponseEl.textContent = data.base_response;
    styledResponseEl.textContent = data.styled_response;
    augmentationEl.textContent = data.style_prompt_augmentation;
    logFileEl.textContent = data.log_file;
    renderScores(data.top_styles);
    renderProviderAttempts(data.provider_attempts);
  } catch (err) {
    bestStyleEl.textContent = "error";
    baseProviderEl.textContent = "-";
    alignmentProviderEl.textContent = "-";
    baseSourceEl.textContent = "-";
    retrievalModelEl.textContent = "-";
    baseResponseEl.textContent = "Error: " + err.message;
    styledResponseEl.textContent = "Error: " + err.message;
    augmentationEl.textContent = "Backend error. Check the Flask terminal.";
    providerAttemptsEl.textContent = "-";
    logFileEl.textContent = "-";
    scoresEl.innerHTML = "";
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "Run Alignment";
  }
}
