// =============================================
// DIGI-SCHOOL AI — Attendance Page (Live Data)
// =============================================

import '../styles/pages.css';
import { renderSidebar }              from '../components/sidebar.js';
import { renderVoiceBar, initVoiceBar } from '../components/voiceBar.js';
import { api }                        from '../api.js';
import { renderPageShell, renderPageError } from '../utils/pageUtils.js';

// ─── Helpers ─────────────────────────────────

function attSummary(records) {
  return {
    present: records.filter(r => r.status === 'P').length,
    absent:  records.filter(r => r.status === 'A').length,
    late:    records.filter(r => r.status === 'L').length,
    excused: records.filter(r => r.status === 'E').length,
  };
}

// ─── Student row ─────────────────────────────

function renderStudentRow(student, attByStudent, dates) {
  const records = attByStudent[student.id] ?? {};

  const dateCells = dates.map(date => {
    const status = records[date] ?? '—';
    const cls    = status === '—' ? '' : status;
    return `<td class="att-cell"><span class="att-dot ${cls}">${status}</span></td>`;
  }).join('');

  const allStatuses = dates.map(d => records[d]).filter(Boolean);
  const summary     = attSummary(allStatuses.map(s => ({ status: s })));
  const behavKey    = (student.behavior ?? 'Good').replace(/\s+/g, '-');

  return `
    <tr>
      <td class="student-name-cell">${student.name}</td>
      ${dateCells}
      <td>
        <div class="att-summary">
          ${summary.present  ? `<span class="att-chip P">${summary.present}P</span>`  : ''}
          ${summary.absent   ? `<span class="att-chip A">${summary.absent}A</span>`   : ''}
          ${summary.late     ? `<span class="att-chip L">${summary.late}L</span>`     : ''}
          ${summary.excused  ? `<span class="att-chip E">${summary.excused}E</span>`  : ''}
          ${!summary.absent && !summary.late && !summary.excused && !summary.present
            ? '<span style="font-size:12px;color:var(--text-light)">No records</span>' : ''}
        </div>
      </td>
      <td><span class="behavior-badge behavior-${behavKey}">${student.behavior ?? 'Good'}</span></td>
      <td class="notes-cell">${student.notes || '—'}</td>
    </tr>
  `;
}

// ─── Class accordion ─────────────────────────

function renderClassBlock(cls, students, attRecords, dates, index) {
  const classStudents   = students.filter(s => s.class_id === cls.id);
  const totalStudents   = classStudents.length;
  const presentToday    = cls.present_today ?? 0;
  const pct             = totalStudents > 0 ? Math.round((presentToday / totalStudents) * 100) : 0;
  const isOpen          = index === 0 ? 'open' : '';

  // index att records: { studentId: { date: status } }
  const attByStudent = {};
  attRecords.forEach(r => {
    if (!attByStudent[r.student_id]) attByStudent[r.student_id] = {};
    attByStudent[r.student_id][r.date?.slice(0,10)] = r.status;
  });

  const dateHeaders = dates.map(d => `<th>${d}</th>`).join('');
  const rows = classStudents.length
    ? classStudents.map(s => renderStudentRow(s, attByStudent, dates)).join('')
    : `<tr><td colspan="${dates.length + 4}" class="empty-state">No students in this class yet.</td></tr>`;

  return `
    <div class="accordion-card ${isOpen}" data-acc="${cls.id}">
      <div class="accordion-trigger" onclick="toggleAtt('${cls.id}')">
        <div class="acc-color" style="background:${cls.color}"></div>
        <div class="acc-info">
          <div class="acc-name">${cls.name}</div>
          <div class="acc-meta">${totalStudents} students · ${cls.period ?? ''} · ${cls.room ?? ''}</div>
        </div>
        <div class="acc-stats">
          <div class="acc-stat">
            <div class="acc-stat-value" style="color:var(--green-mid)">${presentToday}</div>
            <div class="acc-stat-label">Present</div>
          </div>
          <div class="acc-stat">
            <div class="acc-stat-value" style="color:var(--warn)">${totalStudents - presentToday}</div>
            <div class="acc-stat-label">Absent</div>
          </div>
          <div class="acc-stat">
            <div class="acc-stat-value">${pct}%</div>
            <div class="acc-stat-label">Rate</div>
          </div>
        </div>
        <span class="acc-chevron">▼</span>
      </div>
      <div class="accordion-body">
        <table class="student-table">
          <thead><tr><th>Student</th>${dateHeaders}<th>Summary</th><th>Behavior</th><th>Notes</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

// ─── Main Render ─────────────────────────────

export async function renderAttendance(appEl) {
  const main = renderPageShell(appEl, 'attendance',
    '📋 <span>Attendance</span> Tracker',
    'Loading attendance data...',
    renderSidebar
  );

  try {
    const [classesRes, studentsRes] = await Promise.all([
      api.classes.getAll(),
      api.students.getAll(),
    ]);

    const classes  = classesRes.classes  ?? [];
    const students = studentsRes.students ?? [];

    // fetch attendance for each class (last 7 days)
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 6);
    const startDate = sevenDaysAgo.toISOString().split('T')[0];

    // build last 7 dates for headers
    const dates = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      dates.push(d.toISOString().split('T')[0]);
    }

    // fetch attendance per class in parallel
    const attResults = await Promise.all(
      classes.map(cls => api.attendance.get(cls.id).then(r => ({ classId: cls.id, records: r.attendance ?? [] })))
    );
    const attByClass = {};
    attResults.forEach(r => { attByClass[r.classId] = r.records; });

    const dateLabels = dates.map(d => {
      const dt = new Date(d);
      return dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    });

    const accordions = classes.map((cls, i) =>
      renderClassBlock(cls, students, attByClass[cls.id] ?? [], dates, i)
    ).join('');

    main.innerHTML = `
      <div class="page-header">
        <div>
          <div class="page-title">📋 <span>Attendance</span> Tracker</div>
          <div class="page-subtitle">Last 7 days · ${classes.length} classes · Click to expand</div>
        </div>
        <div class="header-actions">
          <button class="btn btn-outline" id="exportAttBtn">📄 Export</button>
        </div>
      </div>
      ${renderVoiceBar()}
      <div class="class-accordion">${accordions}</div>
    `;

    window.toggleAtt = id => document.querySelector(`[data-acc="${id}"]`)?.classList.toggle('open');

    initVoiceBar({ onSubmit: text => console.log('[Attendance] Voice:', text) });
    document.getElementById('exportAttBtn')?.addEventListener('click', () => console.log('[Attendance] Export'));

  } catch (err) {
    console.error('[Attendance] Error:', err.message);
    main.innerHTML = renderPageError(err.message, 'attendance');
  }
}