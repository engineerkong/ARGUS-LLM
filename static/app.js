function toggleRetrieved() {
  const body = document.getElementById("retrieved-body");
  const arrow = document.getElementById("retrieved-arrow");
  body.classList.toggle("collapsed");
  arrow.classList.toggle("open");
}

async function submitQuery() {
  const prompt = document.getElementById("prompt").value.trim();
  if (!prompt) { alert("Please enter a prompt."); return; }

  const model = document.getElementById("model").value.trim();
  const intent = document.getElementById("intent").value;
  const dataset_path = document.getElementById("dataset-path").value.trim();

  const btn = document.getElementById("submit-btn");
  const btnText = document.getElementById("btn-text");
  const spinner = document.getElementById("btn-spinner");
  const answerBox = document.getElementById("llm-answer");
  const retrievedContent = document.getElementById("retrieved-content");
  const retrievedBody = document.getElementById("retrieved-body");
  const retrievedArrow = document.getElementById("retrieved-arrow");

  // Loading state
  btn.disabled = true;
  btnText.textContent = "Querying...";
  spinner.classList.remove("hidden");
  answerBox.innerHTML = '<span class="placeholder">Thinking...</span>';
  retrievedContent.textContent = "";

  try {
    const payload = { query: prompt, intent, model };
    if (dataset_path) payload.dataset_path = dataset_path;

    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      answerBox.innerHTML = `<span class="error-text">Error: ${data.error || JSON.stringify(data)}</span>`;
      return;
    }

    // Display answer
    answerBox.textContent = data.response || "(no response)";

    // Display retrieved info (expand if there's content)
    if (data.retrieved && data.retrieved.length > 0) {
      retrievedContent.textContent = formatRetrieved(data.retrieved);
      // Auto-expand
      if (retrievedBody.classList.contains("collapsed")) {
        retrievedBody.classList.remove("collapsed");
        retrievedArrow.classList.add("open");
      }
    } else {
      retrievedContent.textContent = "(no retrieved documents)";
    }

  } catch (e) {
    answerBox.innerHTML = `<span class="error-text">Request failed: ${e.toString()}</span>`;
  } finally {
    btn.disabled = false;
    btnText.textContent = "Submit";
    spinner.classList.add("hidden");
  }
}

function formatRetrieved(items) {
  return items.map((item, i) => {
    const score = item.score != null ? ` | score: ${Number(item.score).toFixed(3)}` : "";
    const source = item.source ? ` | source: ${item.source}` : "";
    return `[${i + 1}]${source}${score}\n${item.text || ""}`;
  }).join("\n\n---\n\n");
}

// Allow Ctrl+Enter to submit
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("prompt").addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key === "Enter") submitQuery();
  });
});
