// =============================================
// DIGI-SCHOOL AI — Flagged Students (Live Data)
// =============================================

import '../styles/pages.css';
import { renderSidebar }  from '../components/sidebar.js';
import { api }            from '../api.js';
import { renderPageShell, renderPageError } from '../utils/pageUtils.js';

const typeConfig = {
  behavior: { label:'Behavior', icon:'⚠️', tagClass:'tag-behavior', bg:'#fde8e4', border:'#f5c6c0', dot:'#e76f51' },
  absence:  { label:'Absence',  icon:'📋', tagClass:'tag-absence',  bg:'#fdebd0', border:'#f5d5a8', dot:'#e67e22' },
  grade:    { label:'Grades',   icon:'📉', tagClass:'tag-grade',    bg:'#fef9e7', border:'#f0d97a', dot:'#d4a017' },
};

function renderFlagCard(student) {
  const cfg = typeConfig[student.type] ?? typeConfig.behavior;
  return `
    <div class="flag-card" style="border-left:4px solid ${cfg.dot}">
      <div class="flag-card-top">
        <div class="flag-card-left">
          <div class="flag-icon-wrap" style="background:${cfg.bg}">${cfg.icon}</div>
          <div>
            <div class="flag-student-name">${student.student_name}</div>
            <div class="flag-student-meta">Class ${student.class_name}</div>
          </div>
        </div>
        <span class="flag-tag ${cfg.tagClass}">${cfg.label}</span>
      </div>
      <div class="flag-reason-box" style="background:${cfg.bg};border:1px solid ${cfg.border}">
        <span class="flag-reason-label">Reason</span>
        <p class="flag-reason-text">${student.reason}</p>
      </div>
      <div class="flag-card-actions">
        <button class="btn btn-outline flag-btn" onclick="draftNotif('${student.student_id}')">📨 Draft Notification</button>
        <button class="flag-btn-resolve" onclick="resolveFlag('${student.id}', this)">✓ Mark Resolved</button>
      </div>
    </div>
  `;
}

function renderSection(type, items) {
  const cfg = typeConfig[type];
  if (!items.length) return '';
  return `
    <div class="flag-section">
      <div class="flag-section-header">
        <span>${cfg.icon}</span><span>${cfg.label} Flags</span>
        <span class="flag-count">${items.length}</span>
      </div>
      <div class="flag-cards-grid">${items.map(renderFlagCard).join('')}</div>
    </div>
  `;
}

export async function renderFlagged(appEl) {
  const main = renderPageShell(appEl, 'flagged', '🚩 <span>Flagged</span> Students', 'Loading...', renderSidebar);

  try {
    const { flagged } = await api.flagged.getAll();
    const list = flagged ?? [];

    main.innerHTML = `
      <div class="page-header">
        <div>
          <div class="page-title">🚩 <span>Flagged</span> Students</div>
          <div class="page-subtitle">${list.length} active flag${list.length !== 1 ? 's' : ''} · Review and take action</div>
        </div>
        <div class="header-actions"><button class="btn btn-outline">📄 Export</button></div>
      </div>
      <div class="flag-page-body">
        ${list.length
          ? ['behavior','absence','grade'].map(t => renderSection(t, list.filter(f => f.type === t))).join('')
          : '<div class="empty-state" style="padding:60px;text-align:center;color:var(--text-light);font-size:14px">🎉 No flagged students right now</div>'
        }
      </div>
      <style>
        .flag-page-body { display:flex; flex-direction:column; gap:28px; animation:fadeUp 0.4s ease 0.1s both; }
        .flag-section-header { display:flex; align-items:center; gap:8px; font-family:var(--font-display); font-size:17px; color:var(--text-dark); margin-bottom:14px; }
        .flag-count { background:var(--warn); color:white; font-family:var(--font-body); font-size:11px; font-weight:700; padding:2px 8px; border-radius:20px; }
        .flag-cards-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:16px; }
        .flag-card { background:white; border-radius:var(--radius); box-shadow:var(--card-shadow); padding:20px; display:flex; flex-direction:column; gap:14px; transition:transform 0.18s; }
        .flag-card:hover { transform:translateY(-2px); }
        .flag-card-top { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
        .flag-card-left { display:flex; align-items:center; gap:12px; }
        .flag-icon-wrap { width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; }
        .flag-student-name { font-size:15px; font-weight:600; color:var(--text-dark); }
        .flag-student-meta { font-size:12px; color:var(--text-light); margin-top:2px; }
        .flag-reason-box { border-radius:var(--radius-sm); padding:12px 14px; }
        .flag-reason-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-light); display:block; margin-bottom:4px; }
        .flag-reason-text { font-size:13px; color:var(--text-dark); line-height:1.5; }
        .flag-card-actions { display:flex; gap:10px; align-items:center; }
        .flag-btn { flex:1; justify-content:center; font-size:12px; padding:7px 14px; }
        .flag-btn-resolve { padding:7px 14px; border-radius:50px; font-size:12px; font-weight:500; font-family:var(--font-body); background:var(--green-pale); color:var(--green-deep); border:none; cursor:pointer; transition:all 0.18s; white-space:nowrap; }
        .flag-btn-resolve:hover { background:var(--green-light); color:white; }
      </style>
    `;

    window.draftNotif = (studentId) => window.navigateTo('notifications');

    window.resolveFlag = async (flagId, btn) => {
      try {
        await api.flagged.resolve(flagId);
        const card = btn.closest('.flag-card');
        card.style.opacity = '0';
        card.style.transition = 'opacity 0.3s';
        setTimeout(() => card.remove(), 300);
      } catch (err) {
        alert('Could not resolve flag: ' + err.message);
      }
    };

  } catch (err) {
    console.error('[Flagged] Error:', err.message);
    main.innerHTML = renderPageError(err.message, 'flagged');
  }
}