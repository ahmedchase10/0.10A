// =============================================
// DIGI-SCHOOL AI — Homework (Live Data)
// =============================================

import '../styles/pages.css';
import { renderSidebar }              from '../components/sidebar.js';
import { renderVoiceBar, initVoiceBar } from '../components/voiceBar.js';
import { api }                        from '../api.js';
import { renderPageShell, renderPageError } from '../utils/pageUtils.js';

function renderHwRow(hw) {
  const isActive = hw.status === 'active';
  return `
    <tr style="${!isActive ? 'opacity:0.6' : ''}">
      <td class="student-name-cell">${hw.title}</td>
      <td style="font-size:12px;color:var(--text-mid)">${hw.subject || '—'}</td>
      <td style="font-size:12px;color:var(--text-mid)">${hw.chapter || '—'}</td>
      <td style="font-size:12px;color:var(--text-light);white-space:nowrap">
        ${new Date(hw.assigned_date).toLocaleDateString('en-GB',{day:'numeric',month:'short'})}
      </td>
      <td style="font-size:12px;font-weight:600;white-space:nowrap;color:${isActive ? 'var(--warn)' : 'var(--text-light)'}">
        ${new Date(hw.due_date).toLocaleDateString('en-GB',{day:'numeric',month:'short'})}
      </td>
      <td>
        <span class="hw-status-chip ${hw.status}">${isActive ? '⏳ Active' : '✓ Done'}</span>
      </td>
      ${isActive ? `<td><button class="btn btn-outline" style="font-size:11px;padding:4px 10px" onclick="completeHw(${hw.id}, this)">Mark Done</button></td>` : '<td></td>'}
    </tr>
  `;
}

function renderClassBlock(cls, homework, index) {
  const active    = homework.filter(h => h.status === 'active').length;
  const completed = homework.filter(h => h.status === 'completed').length;
  const isOpen    = index === 0 ? 'open' : '';
  const rows      = homework.length
    ? homework.map(renderHwRow).join('')
    : `<tr><td colspan="7" class="empty-state">No homework logged yet.</td></tr>`;

  return `
    <div class="accordion-card ${isOpen}" data-acc="hw-${cls.id}">
      <div class="accordion-trigger" onclick="toggleHw('hw-${cls.id}')">
        <div class="acc-color" style="background:${cls.color}"></div>
        <div class="acc-info">
          <div class="acc-name">${cls.name}</div>
          <div class="acc-meta">${cls.period ?? ''} · ${cls.room ?? ''}</div>
        </div>
        <div class="acc-stats">
          <div class="acc-stat"><div class="acc-stat-value" style="color:var(--warn)">${active}</div><div class="acc-stat-label">Active</div></div>
          <div class="acc-stat"><div class="acc-stat-value" style="color:var(--green-mid)">${completed}</div><div class="acc-stat-label">Done</div></div>
          <div class="acc-stat"><div class="acc-stat-value">${homework.length}</div><div class="acc-stat-label">Total</div></div>
        </div>
        <span class="acc-chevron">▼</span>
      </div>
      <div class="accordion-body">
        <table class="student-table">
          <thead><tr><th>Assignment</th><th>Subject</th><th>Chapter</th><th>Assigned</th><th>Due</th><th>Status</th><th></th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

export async function renderHomework(appEl) {
  const main = renderPageShell(appEl, 'homework', '🏠 <span>Homework</span> Tracker', 'Loading...', renderSidebar);

  try {
    const [classesRes, hwRes] = await Promise.all([
      api.classes.getAll(),
      api.homework.get(),
    ]);
    const classes  = classesRes.classes    ?? [];
    const homework = hwRes.homework        ?? [];
    const byClass  = {};
    classes.forEach(c => { byClass[c.id] = []; });
    homework.forEach(h => { if (byClass[h.class_id]) byClass[h.class_id].push(h); });

    const totalActive = homework.filter(h => h.status === 'active').length;
    const accordions  = classes.map((cls, i) => renderClassBlock(cls, byClass[cls.id] ?? [], i)).join('');

    main.innerHTML = `
      <div class="page-header">
        <div>
          <div class="page-title">🏠 <span>Homework</span> Tracker</div>
          <div class="page-subtitle">${totalActive} active assignment${totalActive !== 1 ? 's' : ''} · All classes</div>
        </div>
        <div class="header-actions"><button class="btn btn-outline">📄 Export</button></div>
      </div>
      ${renderVoiceBar()}
      <div class="class-accordion">${accordions}</div>
      <style>
        .hw-status-chip { font-size:11px; font-weight:600; padding:3px 10px; border-radius:20px; white-space:nowrap; }
        .hw-status-chip.active    { background:#fdebd0; color:var(--warn); }
        .hw-status-chip.completed { background:var(--green-pale); color:var(--green-mid); }
      </style>
    `;

    window.toggleHw = id => document.querySelector(`[data-acc="${id}"]`)?.classList.toggle('open');

    window.completeHw = async (id, btn) => {
      try {
        await api.homework.complete(id);
        const row = btn.closest('tr');
        row.style.opacity = '0.6';
        btn.remove();
        row.querySelector('.hw-status-chip').className = 'hw-status-chip completed';
        row.querySelector('.hw-status-chip').textContent = '✓ Done';
      } catch (err) { alert('Error: ' + err.message); }
    };

    initVoiceBar({ onSubmit: text => console.log('[Homework] Voice:', text) });

  } catch (err) {
    console.error('[Homework] Error:', err.message);
    main.innerHTML = renderPageError(err.message, 'homework');
  }
}