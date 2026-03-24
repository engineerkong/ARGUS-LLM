const INTENT_DESC = {
  annotation: "Provide the most accurate description and unit for a term by identifying its meaning from public knowledge bases.",
  query:      "Answer questions by querying and retrieving relevant content from the internal pilot database.",
  decision:   "Validate the reliability of decision-making actions according to retrieved content from relevant pilot databases."
};

function selectTab(btn) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const intent = btn.dataset.intent;
  document.getElementById('intent').value = intent;
  document.getElementById('intent-desc').textContent = INTENT_DESC[intent] || '';

  const datasetField = document.getElementById('dataset-field');
  datasetField.style.display = (intent === 'query' || intent === 'decision') ? 'flex' : 'none';
}

function toggleRetrieved() {
  const body  = document.getElementById('retrieved-body');
  const arrow = document.getElementById('retrieved-arrow');
  body.classList.toggle('collapsed');
  arrow.classList.toggle('open');
}

async function submitQuery() {
  const prompt = document.getElementById('prompt').value.trim();
  if (!prompt) { alert('Please enter a prompt.'); return; }

  const model       = document.getElementById('model').value.trim();
  const intent      = document.getElementById('intent').value;
  const datasetPath = document.getElementById('dataset-path').value.trim();

  const btn        = document.getElementById('submit-btn');
  const btnText    = document.getElementById('btn-text');
  const spinner    = document.getElementById('btn-spinner');
  const answerBox  = document.getElementById('llm-answer');
  const retrieved  = document.getElementById('retrieved-content');
  const resultCard = document.getElementById('results-card');

  // Loading state
  btn.disabled = true;
  btnText.textContent = 'Querying…';
  spinner.classList.remove('hidden');
  answerBox.innerHTML = '<span class="placeholder">Thinking…</span>';
  retrieved.textContent = '';
  resultCard.style.display = 'flex';

  // Collapse retrieved panel while loading
  const retrievedBody  = document.getElementById('retrieved-body');
  const retrievedArrow = document.getElementById('retrieved-arrow');
  retrievedBody.classList.add('collapsed');
  retrievedArrow.classList.remove('open');

  try {
    const payload = { query: prompt, intent, model };
    if (datasetPath) payload.dataset_path = datasetPath;

    const res  = await fetch('/api/query', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      answerBox.innerHTML = `<span class="error-text">Error: ${data.error || JSON.stringify(data)}</span>`;
      return;
    }

    answerBox.textContent = data.response || '(no response)';

    if (data.retrieved && data.retrieved.length > 0) {
      retrieved.textContent = formatRetrieved(data.retrieved);
      retrievedBody.classList.remove('collapsed');
      retrievedArrow.classList.add('open');
    } else {
      retrieved.textContent = '(no retrieved documents)';
    }

  } catch (e) {
    answerBox.innerHTML = `<span class="error-text">Request failed: ${e.toString()}</span>`;
  } finally {
    btn.disabled = false;
    btnText.textContent = 'Submit';
    spinner.classList.add('hidden');
  }
}

function formatRetrieved(items) {
  return items.map((item, i) => {
    const score  = item.score  != null ? ` | score: ${Number(item.score).toFixed(3)}` : '';
    const source = item.source ? ` | source: ${item.source}` : '';
    return `[${i + 1}]${source}${score}\n${item.text || ''}`;
  }).join('\n\n---\n\n');
}

// Ctrl+Enter to submit
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('prompt').addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 'Enter') submitQuery();
  });
});
