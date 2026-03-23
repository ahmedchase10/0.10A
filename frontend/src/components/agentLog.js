// =============================================
// COMPONENT: Agent Log
// Accepts live voice history as parameter
// =============================================

// ─── Agent status bar ───────────────────────

export function renderAgentBar(lastEntry = null) {
  const summary = lastEntry
    ? `<strong>Last voice note</strong> — ${lastEntry.actions_count} action${lastEntry.actions_count !== 1 ? 's' : ''} executed on ${lastEntry.class_name} · ${new Date(lastEntry.recorded_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`
    : `<strong>Agent ready</strong> — speak or type a note to get started`;

  return `
    <div class="agent-bar">
      <div class="agent-pulse"></div>
      <div class="agent-text">${summary}</div>
      <div class="agent-actions">
        <button class="agent-btn agent-btn-approve" id="agentApproveBtn">✓ Approve All</button>
        <button class="agent-btn agent-btn-review"  id="agentReviewBtn">Review</button>
      </div>
    </div>
  `;
}

// ─── Agent log card ─────────────────────────

export function renderAgentLogCard(voiceHistory = []) {
  const today      = new Date().toDateString();
  const todayItems = voiceHistory.filter(v =>
    new Date(v.recorded_at).toDateString() === today
  );

  const items = todayItems.length
    ? todayItems.flatMap(entry => {
        const actions = Array.isArray(entry.actions_json) ? entry.actions_json : [];
        const time = new Date(entry.recorded_at).toLocaleTimeString('en-GB', {
          hour: '2-digit', minute: '2-digit',
        });
        return actions.map((action, i) => `
          <div class="activity-item">
            <div class="activity-time">${i === 0 ? time : ''}</div>
            <div class="activity-dot filled"></div>
            <div class="activity-text">
              <strong>${entry.class_name}</strong> — ${action.label ?? action}
            </div>
          </div>
        `);
      }).join('')
    : `<div style="padding:20px;text-align:center;color:var(--text-light);font-size:13px;">No agent actions today yet.</div>`;

  return `
    <div class="card">
      <div class="card-header">
        <div class="card-title">Today's Agent Log</div>
        <span class="card-action" onclick="navigateTo('voice')" style="cursor:pointer">Full history →</span>
      </div>
      <div class="activity-list">${items}</div>
    </div>
  `;
}

// ─── Init listeners ──────────────────────────

export function initAgentBar({ onApprove, onReview } = {}) {
  document.getElementById('agentApproveBtn')?.addEventListener('click', () => {
    if (typeof onApprove === 'function') onApprove();
    else console.log('[AgentLog] All actions approved');
  });

  document.getElementById('agentReviewBtn')?.addEventListener('click', () => {
    if (typeof onReview === 'function') onReview();
    window.navigateTo('voice');
  });
}