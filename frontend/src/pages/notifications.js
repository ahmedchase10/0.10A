// =============================================
// DIGI-SCHOOL AI — Notifications (Live Data)
// =============================================

import '../styles/pages.css';
import { renderSidebar } from '../components/sidebar.js';
import { api }           from '../api.js';
import { renderPageShell, renderPageError } from '../utils/pageUtils.js';

const typeConfig = {
  behavior: { label:'Behavior', tagClass:'tag-behavior', icon:'⚠️' },
  absence:  { label:'Absence',  tagClass:'tag-absence',  icon:'📋' },
  grade:    { label:'Grades',   tagClass:'tag-grade',    icon:'📉' },
};

const defaultMsg = {
  behavior: name => `Dear parent, this is to inform you that ${name} has been involved in repeated classroom disruptions. We kindly request a meeting to discuss the matter.`,
  absence:  name => `Dear parent, we would like to inform you that ${name} has accumulated multiple unexcused absences. Please contact the school at your earliest convenience.`,
  grade:    name => `Dear parent, we wish to bring to your attention that ${name}'s academic performance has declined recently. We recommend scheduling a follow-up discussion.`,
};

function renderDraftCard(student) {
  const cfg = typeConfig[student.type] ?? typeConfig.behavior;
  const msg = defaultMsg[student.type]?.(student.student_name) ?? '';
  const email = student.parent_email || '';
  return `
    <div class="notif-draft-card" id="draft-${student.student_id}">
      <div class="notif-draft-header">
        <div class="notif-draft-who">
          <div class="notif-avatar">${student.student_name.charAt(0)}</div>
          <div>
            <div class="notif-student-name">${student.student_name}</div>
            <div class="notif-student-meta">
              Class ${student.class_name} ·
              ${email
                ? `<a href="mailto:${email}" style="color:var(--green-mid);text-decoration:none">${email}</a>`
                : '<span style="color:var(--warn);font-size:11px">⚠️ No parent email</span>'}
            </div>
          </div>
        </div>
        <span class="flag-tag ${cfg.tagClass}">${cfg.icon} ${cfg.label}</span>
      </div>
      <textarea class="notif-textarea" id="msg-${student.student_id}" rows="4">${msg}</textarea>
      <div class="notif-draft-actions">
        <button class="btn btn-outline notif-btn">🔄 Regenerate</button>
        <button class="btn btn-primary notif-btn"
          onclick="sendNotif('${student.student_id}', '${student.id}', '${student.type}', '${student.class_id}')"
          ${!email ? 'disabled title="No parent email on file"' : ''}>
          📨 Send to Parent
        </button>
      </div>
    </div>
  `;
}

function renderHistoryItem(notif) {
  const cfg = typeConfig[notif.type] ?? typeConfig.behavior;
  return `
    <div class="notif-history-item">
      <div class="notif-history-left">
        <span class="notif-avatar small">${notif.student_name.charAt(0)}</span>
        <div>
          <div class="notif-history-name">${notif.student_name} <span style="color:var(--text-light);font-weight:400">· ${notif.class_name}</span></div>
          <div class="notif-history-msg">${notif.message}</div>
        </div>
      </div>
      <div class="notif-history-right">
        <span class="flag-tag ${cfg.tagClass}">${cfg.label}</span>
        <div class="notif-sent-time">✓ ${new Date(notif.sent_at).toLocaleString('en-GB',{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})}</div>
      </div>
    </div>
  `;
}

export async function renderNotifications(appEl) {
  const main = renderPageShell(appEl, 'notifications', '📨 <span>Parent</span> Notifications', 'Loading...', renderSidebar);

  try {
    const [flaggedRes, historyRes] = await Promise.all([
      api.flagged.getAll(),
      api.notifications.getAll(),
    ]);

    const flagged = flaggedRes.flagged        ?? [];
    const history = historyRes.notifications  ?? [];

    const draftCards   = flagged.map(renderDraftCard).join('');
    const historyItems = history.map(renderHistoryItem).join('');

    main.innerHTML = `
      <div class="page-header">
        <div>
          <div class="page-title">📨 <span>Parent</span> Notifications</div>
          <div class="page-subtitle">Draft and send notifications · Review history</div>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary" id="sendAllBtn">📨 Send All Drafts</button>
        </div>
      </div>

      <div class="notif-section-title">
        <span>✏️ Ready to Send</span>
        <span class="flag-count" style="background:var(--green-mid)">${flagged.length}</span>
      </div>
      <div class="notif-drafts-grid">
        ${draftCards || '<div class="empty-state" style="padding:30px;text-align:center;color:var(--text-light)">No flagged students to notify.</div>'}
      </div>

      <div class="notif-section-title" style="margin-top:8px">
        <span>🕒 Sent History</span>
        <span class="flag-count" style="background:var(--text-light)">${history.length}</span>
      </div>
      <div class="card notif-history-card">
        ${historyItems || '<div class="empty-state" style="padding:30px;text-align:center;color:var(--text-light)">No notifications sent yet.</div>'}
      </div>

      <style>
        .notif-section-title { display:flex; align-items:center; gap:8px; font-family:var(--font-display); font-size:17px; color:var(--text-dark); margin-bottom:14px; animation:fadeUp 0.4s ease 0.05s both; }
        .flag-count { font-family:var(--font-body); font-size:11px; font-weight:700; padding:2px 8px; border-radius:20px; color:white; }
        .notif-drafts-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(360px,1fr)); gap:16px; animation:fadeUp 0.4s ease 0.1s both; margin-bottom:32px; }
        .notif-draft-card { background:white; border-radius:var(--radius); box-shadow:var(--card-shadow); padding:20px; display:flex; flex-direction:column; gap:14px; border:1.5px solid var(--green-pale); transition:border-color 0.2s; }
        .notif-draft-card:focus-within { border-color:var(--green-light); }
        .notif-draft-header { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; }
        .notif-draft-who { display:flex; align-items:center; gap:10px; }
        .notif-avatar { width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,var(--green-mid),var(--green-deep)); color:white; font-weight:700; font-size:14px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .notif-avatar.small { width:30px; height:30px; font-size:12px; }
        .notif-student-name { font-size:14px; font-weight:600; color:var(--text-dark); }
        .notif-student-meta { font-size:12px; color:var(--text-light); margin-top:1px; }
        .notif-textarea { width:100%; border:1.5px solid var(--green-pale); border-radius:var(--radius-sm); padding:12px 14px; font-family:var(--font-body); font-size:13px; color:var(--text-dark); resize:vertical; line-height:1.55; background:var(--cream); transition:border-color 0.2s; }
        .notif-textarea:focus { outline:none; border-color:var(--green-light); background:white; }
        .notif-draft-actions { display:flex; gap:10px; }
        .notif-btn { flex:1; justify-content:center; font-size:12px; padding:8px 14px; }
        .notif-history-card { animation:fadeUp 0.4s ease 0.15s both; }
        .notif-history-item { display:flex; justify-content:space-between; align-items:flex-start; gap:20px; padding:16px 22px; border-bottom:1px solid var(--green-pale); transition:background 0.12s; }
        .notif-history-item:last-child { border-bottom:none; }
        .notif-history-item:hover { background:#f4fbf6; }
        .notif-history-left { display:flex; gap:12px; align-items:flex-start; flex:1; min-width:0; }
        .notif-history-name { font-size:13px; font-weight:600; color:var(--text-dark); margin-bottom:4px; }
        .notif-history-msg { font-size:12px; color:var(--text-mid); line-height:1.45; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:480px; }
        .notif-history-right { display:flex; flex-direction:column; align-items:flex-end; gap:6px; flex-shrink:0; }
        .notif-sent-time { font-size:11px; color:var(--green-mid); white-space:nowrap; }
      </style>
    `;

    window.sendNotif = async (studentId, flagId, type, classId) => {
      const msg = document.getElementById(`msg-${studentId}`)?.value?.trim();
      if (!msg) return;
      try {
        await api.notifications.send({ studentId, classId, type, message: msg });
        const card = document.getElementById(`draft-${studentId}`);
        if (card) {
          card.style.opacity = '0.5';
          card.style.pointerEvents = 'none';
          card.insertAdjacentHTML('afterbegin', '<div style="text-align:center;color:var(--green-mid);font-size:13px;font-weight:600;padding:4px 0">✓ Sent</div>');
        }
      } catch (err) { alert('Failed to send: ' + err.message); }
    };

    document.getElementById('sendAllBtn')?.addEventListener('click', () => {
      flagged.forEach(s => window.sendNotif(s.student_id, s.id, s.type, s.class_id));
    });

  } catch (err) {
    console.error('[Notifications] Error:', err.message);
    main.innerHTML = renderPageError(err.message, 'notifications');
  }
}