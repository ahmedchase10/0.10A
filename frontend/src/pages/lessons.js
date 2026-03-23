// =============================================
// DIGI-SCHOOL AI — Lesson Log (Live Data)
// =============================================

import '../styles/pages.css';
import { renderSidebar }              from '../components/sidebar.js';
import { renderVoiceBar, initVoiceBar } from '../components/voiceBar.js';
import { api }                        from '../api.js';
import { renderPageShell, renderPageError } from '../utils/pageUtils.js';

function renderLessonRow(lesson) {
  return `
    <tr>
      <td style="color:var(--text-light);font-size:12px;white-space:nowrap">
        ${new Date(lesson.date).toLocaleDateString('en-GB',{day:'numeric',month:'short'})}
      </td>
      <td class="student-name-cell">${lesson.chapter || '—'}</td>
      <td style="font-size:13px;color:var(--text-mid)">${lesson.topic || '—'}</td>
      <td>
        ${lesson.weak_point
          ? `<span class="weak-point-chip">⚠️ ${lesson.weak_point}</span>`
          : `<span style="font-size:12px;color:var(--green-mid)">None noted</span>`}
      </td>
      <td class="notes-cell">
        ${lesson.insight ? `<span style="color:var(--green-mid)">💡 ${lesson.insight}</span>` : '—'}
      </td>
    </tr>
  `;
}

function renderClassBlock(cls, lessons, index) {
  const weakCount = lessons.filter(l => l.weak_point).length;
  const isOpen    = index === 0 ? 'open' : '';
  const rows      = lessons.length
    ? lessons.map(renderLessonRow).join('')
    : `<tr><td colspan="5" class="empty-state">No lessons logged yet.</td></tr>`;

  return `
    <div class="accordion-card ${isOpen}" data-acc="log-${cls.id}">
      <div class="accordion-trigger" onclick="toggleLogs('log-${cls.id}')">
        <div class="acc-color" style="background:${cls.color}"></div>
        <div class="acc-info">
          <div class="acc-name">${cls.name}</div>
          <div class="acc-meta">${cls.period ?? ''} · ${cls.room ?? ''}</div>
        </div>
        <div class="acc-stats">
          <div class="acc-stat"><div class="acc-stat-value">${lessons.length}</div><div class="acc-stat-label">Lessons</div></div>
          <div class="acc-stat"><div class="acc-stat-value" style="${weakCount ? 'color:var(--warn)' : 'color:var(--green-mid)'}">${weakCount}</div><div class="acc-stat-label">Weak Points</div></div>
        </div>
        <span class="acc-chevron">▼</span>
      </div>
      <div class="accordion-body">
        <table class="student-table">
          <thead><tr><th>Date</th><th>Chapter</th><th>Topic</th><th>Weak Point</th><th>Agent Insight</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

export async function renderLessons(appEl) {
  const main = renderPageShell(appEl, 'lessons', '📚 <span>Lesson</span> Log', 'Loading...', renderSidebar);

  try {
    const [classesRes, lessonsRes] = await Promise.all([
      api.classes.getAll(),
      api.lessons.get(),
    ]);
    const classes = classesRes.classes  ?? [];
    const lessons = lessonsRes.lessons  ?? [];
    const byClass = {};
    classes.forEach(c => { byClass[c.id] = []; });
    lessons.forEach(l => { if (byClass[l.class_id]) byClass[l.class_id].push(l); });

    const accordions = classes.map((cls, i) => renderClassBlock(cls, byClass[cls.id] ?? [], i)).join('');

    main.innerHTML = `
      <div class="page-header">
        <div>
          <div class="page-title">📚 <span>Lesson</span> Log</div>
          <div class="page-subtitle">Teaching history · Weak points · Agent insights</div>
        </div>
        <div class="header-actions"><button class="btn btn-outline">📄 Export</button></div>
      </div>
      ${renderVoiceBar()}
      <div class="class-accordion">${accordions}</div>
      <style>
        .weak-point-chip { display:inline-block; background:#fdebd0; color:var(--warn); font-size:11px; font-weight:600; padding:3px 10px; border-radius:20px; }
      </style>
    `;

    window.toggleLogs = id => document.querySelector(`[data-acc="${id}"]`)?.classList.toggle('open');
    initVoiceBar({ onSubmit: text => console.log('[Lessons] Voice:', text) });

  } catch (err) {
    console.error('[Lessons] Error:', err.message);
    main.innerHTML = renderPageError(err.message, 'lessons');
  }
}