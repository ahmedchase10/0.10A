// =============================================
// DIGI-SCHOOL AI — Students Page (Live Data)
// =============================================

import '../styles/pages.css';
import { renderSidebar }              from '../components/sidebar.js';
import { renderVoiceBar, initVoiceBar } from '../components/voiceBar.js';
import { api }                        from '../api.js';
import { renderPageShell, renderPageError } from '../utils/pageUtils.js';

function avgClass(avg) {
  const n = parseFloat(avg);
  if (n >= 16) return 'grade-high';
  if (n >= 12) return 'grade-mid';
  return 'grade-low';
}

function getAvg(gradeMap) {
  const vals = Object.values(gradeMap ?? {});
  if (!vals.length) return null;
  return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
}

function indexGrades(gradeRecords) {
  const map = {};
  gradeRecords.forEach(g => {
    if (!map[g.student_id]) map[g.student_id] = {};
    map[g.student_id][g.subject] = parseFloat(g.score);
  });
  return map;
}

function attRate(attRecords) {
  if (!attRecords.length) return null;
  const present = attRecords.filter(r => r.status === 'P' || r.status === 'L').length;
  return Math.round((present / attRecords.length) * 100);
}

function indexAtt(attRecords) {
  const map = {};
  attRecords.forEach(r => {
    if (!map[r.student_id]) map[r.student_id] = [];
    map[r.student_id].push(r);
  });
  return map;
}

function renderStudentRow(student, gradeMap, attRecords, flaggedIds) {
  const avg      = getAvg(gradeMap);
  const rate     = attRate(attRecords);
  const absent   = attRecords.filter(r => r.status === 'A').length;
  const late     = attRecords.filter(r => r.status === 'L').length;
  const excused  = attRecords.filter(r => r.status === 'E').length;
  const flagged  = flaggedIds.has(student.id);
  const behavKey = (student.behavior ?? 'Good').replace(/\s+/g, '-');
  const rateColor = rate == null ? 'var(--text-light)' : rate >= 90 ? 'var(--green-mid)' : rate >= 75 ? 'var(--gold)' : 'var(--warn)';

  return `
    <tr>
      <td class="student-name-cell">
        ${student.name}
        ${flagged ? '<span class="flag-inline">🚩</span>' : ''}
      </td>
      <td class="avg-cell ${avgClass(avg)}">${avg ?? '—'}<span style="font-size:10px;color:var(--text-light)">/20</span></td>
      <td>
        ${rate != null ? `
          <div style="display:flex;align-items:center;gap:8px">
            <div style="width:60px;height:5px;background:var(--green-pale);border-radius:99px;overflow:hidden">
              <div style="width:${rate}%;height:100%;background:${rateColor};border-radius:99px"></div>
            </div>
            <span style="font-size:12px;font-weight:600;color:${rateColor}">${rate}%</span>
          </div>` : '<span style="font-size:12px;color:var(--text-light)">No data</span>'}
      </td>
      <td>
        <div class="att-summary">
          ${absent  ? `<span class="att-chip A">${absent}A</span>`  : ''}
          ${late    ? `<span class="att-chip L">${late}L</span>`    : ''}
          ${excused ? `<span class="att-chip E">${excused}E</span>` : ''}
          ${!absent && !late && !excused ? '<span style="font-size:12px;color:var(--green-mid)">All present</span>' : ''}
        </div>
      </td>
      <td><span class="behavior-badge behavior-${behavKey}">${student.behavior ?? 'Good'}</span></td>
      <td style="font-size:12px;color:var(--text-mid)">
        ${student.parent_email
          ? `<a href="mailto:${student.parent_email}" style="color:var(--green-mid);text-decoration:none">${student.parent_email}</a>`
          : '<span style="color:var(--text-light)">—</span>'}
      </td>
      <td class="notes-cell">${student.notes || '—'}</td>
    </tr>
  `;
}

function renderClassBlock(cls, students, gradeIndex, attIndex, flaggedIds, index) {
  const classStudents = students.filter(s => s.class_id === cls.id);
  const avgGrade = classStudents.length
    ? (classStudents.reduce((sum, s) => sum + (parseFloat(getAvg(gradeIndex[s.id])) || 0), 0) / classStudents.length).toFixed(1)
    : '—';
  const flaggedCount = classStudents.filter(s => flaggedIds.has(s.id)).length;
  const isOpen = index === 0 ? 'open' : '';
  const rows = classStudents.length
    ? classStudents.map(s => renderStudentRow(s, gradeIndex[s.id] ?? {}, attIndex[s.id] ?? [], flaggedIds)).join('')
    : `<tr><td colspan="6" class="empty-state">No students yet.</td></tr>`;

  return `
    <div class="accordion-card ${isOpen}" data-acc="stu-${cls.id}">
      <div class="accordion-trigger" onclick="toggleStudents('stu-${cls.id}')">
        <div class="acc-color" style="background:${cls.color}"></div>
        <div class="acc-info">
          <div class="acc-name">${cls.name}</div>
          <div class="acc-meta">${classStudents.length} students · ${cls.period ?? ''} · ${cls.room ?? ''}</div>
        </div>
        <div class="acc-stats">
          <div class="acc-stat"><div class="acc-stat-value">${classStudents.length}</div><div class="acc-stat-label">Students</div></div>
          <div class="acc-stat"><div class="acc-stat-value ${avgClass(avgGrade)}">${avgGrade}</div><div class="acc-stat-label">Avg Grade</div></div>
          <div class="acc-stat"><div class="acc-stat-value" style="${flaggedCount ? 'color:var(--warn)' : 'color:var(--green-mid)'}">${flaggedCount}</div><div class="acc-stat-label">Flagged</div></div>
        </div>
        <span class="acc-chevron">▼</span>
      </div>
      <div class="accordion-body">
        <table class="student-table">
          <thead><tr><th>Student</th><th>Avg Grade</th><th>Attendance Rate</th><th>Absences</th><th>Behavior</th><th>Parent Email</th><th>Notes</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

export async function renderStudents(appEl) {
  const main = renderPageShell(appEl, 'students', '👥 <span>Students</span> Roster', 'Loading...', renderSidebar);

  try {
    const [classesRes, studentsRes, gradesRes, flaggedRes, attRes] = await Promise.all([
      api.classes.getAll(),
      api.students.getAll(),
      api.grades.get(),
      api.flagged.getAll(),
      api.attendance.today(),
    ]);

    const classes  = classesRes.classes   ?? [];
    const students = studentsRes.students  ?? [];
    const grades   = gradesRes.grades      ?? [];
    const flagged  = flaggedRes.flagged    ?? [];
    const att      = attRes.attendance     ?? [];

    const gradeIndex = indexGrades(grades);
    const attIndex   = indexAtt(att);
    const flaggedIds = new Set(flagged.map(f => f.student_id));
    const total      = students.length;

    const accordions = classes.map((cls, i) =>
      renderClassBlock(cls, students, gradeIndex, attIndex, flaggedIds, i)
    ).join('');

    main.innerHTML = `
      <div class="page-header">
        <div>
          <div class="page-title">👥 <span>Students</span> Roster</div>
          <div class="page-subtitle">${total} students across ${classes.length} classes · Click to expand</div>
        </div>
        <div class="header-actions"><button class="btn btn-outline">📄 Export</button></div>
      </div>
      ${renderVoiceBar()}
      <div class="class-accordion">${accordions}</div>
      <style>
        .flag-inline { font-size:11px; margin-left:6px; vertical-align:middle; }
      </style>
    `;

    window.toggleStudents = id => document.querySelector(`[data-acc="${id}"]`)?.classList.toggle('open');
    initVoiceBar({ onSubmit: text => console.log('[Students] Voice:', text) });

  } catch (err) {
    console.error('[Students] Error:', err.message);
    main.innerHTML = renderPageError(err.message, 'students');
  }
}