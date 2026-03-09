const chatToggle = document.getElementById('chatToggle');
const chatPanel = document.getElementById('chatPanel');
const chatClose = document.getElementById('chatClose');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');

// Open/close
chatToggle.addEventListener('click', () => chatPanel.classList.toggle('open'));
chatClose.addEventListener('click', () => chatPanel.classList.remove('open'));

// Send on Enter
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
chatSend.addEventListener('click', sendMessage);

function getReportContext() {
  try {
    const raw = sessionStorage.getItem('auditReport');
    if (!raw) return {};
    const d = JSON.parse(raw);
    const best = d.comparison?.[d.best_broker_id] || {};
    return {
      current_broker_name: d.current_broker_name,
      aum: d.portfolio?.aum,
      health_score: d.health?.score,
      health_band: d.health?.band,
      total_cash: d.portfolio?.total_cash,
      sweep_loss: best.sweep?.annual_loss_usd,
      best_broker_name: best.broker_name,
      annual_savings: best.total_annual_savings_usd,
      breakeven_months: best.breakeven_months,
      mutual_fund_flags: d.mutual_fund_flags || [],
    };
  } catch { return {}; }
}

function getSessionId() {
  try {
    const raw = sessionStorage.getItem('auditReport');
    return raw ? JSON.parse(raw).session_id : null;
  } catch { return null; }
}

function appendMessage(text, role) {
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  const bubble = document.createElement('span');
  bubble.className = 'msg-bubble';
  bubble.textContent = text;
  div.appendChild(bubble);
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return bubble;
}

async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;

  chatInput.value = '';
  chatSend.disabled = true;
  appendMessage(text, 'user');

  const typingBubble = appendMessage('Thinking...', 'advisor');
  typingBubble.classList.add('typing');

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        session_id: getSessionId(),
        context: getReportContext(),
      }),
    });
    const data = await res.json();
    typingBubble.classList.remove('typing');
    typingBubble.textContent = data.reply || data.error || 'No response.';
  } catch {
    typingBubble.classList.remove('typing');
    typingBubble.textContent = 'Connection error. Please try again.';
  } finally {
    chatSend.disabled = false;
    chatInput.focus();
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}
