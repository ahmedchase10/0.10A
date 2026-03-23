// =============================================
// DIGI-SCHOOL AI — Grades Page (Live Data)
// =============================================

import '../styles/pages.css';
import { renderSidebar }              from '../components/sidebar.js';
import { renderVoiceBar, initVoiceBar } from '../components/voiceBar.js';
import { api }                        from '../api.js';
import { renderPageShell, renderPageError } from '../utils/pageUtils.js';

// ─── Helpers ─────────────────────────────────

function gradeClass(val) {
  if (val == null) return '';
  if (val >= 16) return 'grade-high';
  if (val >= 12) return 'grade-mid';
  return 'grade-low';
}

function avgClass(avg) {
  const n = parseFloat(avg);
  if (n >= 16) return 'grade-high';
  if (n >= 12) return 'grade-mid';
  return 'grade-low';
}

// ─── Build grade structure ────────────────────
// Returns { studentId: { subject: score } }
function indexGrades(gradeRecords) {
  const map = {};
  gradeRecords.forEach(g => {
    if (!map[g.student_id]) map[g.student_id] = {};
    map[g.student_id][g.subject] = parseFloat(g.score);
  });
  return map;
}

function getAvg(gradeMap) {
  const vals = Object.values(gradeMap);
  if (!vals.length) return null;
  return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
}

// ─── Student row ─────────────────────────────

function renderStudentRow(student, gradeMap, subjects, rank) {
  const avg      = getAvg(gradeMap);
  const behavKey = (student.behavior ?? 'Good').replace(/\s+/g, '-');

  const gradeCells = subjects.map(sub => {
    const val = gradeMap[sub] ?? null;
    return `<td class="grade-cell ${gradeClass(val)}">${val ?? '—'}</td>`;
  }).join('');

  return `
    <tr>
      <td style="color:var(--text-light);font-size:12px;text-align:center">${rank}</td>
      <td class="student-name-cell">${student.name}</td>
      ${gradeCells}
      <td class="avg-cell ${avgClass(avg)}">${avg ?? '—'}</td>
      <td><span class="behavior-badge behavior-${behavKey}">${student.behavior ?? 'Good'}</span></td>
      <td class="notes-cell">${student.notes || '—'}</td>
    </tr>
  `;
}

// ─── Class accordion ─────────────────────────

function renderClassBlock(cls, students, gradeIndex, index) {
  const classStudents = students.filter(s => s.class_id === cls.id);

  // collect all subjects across this class
  const subjectSet = new Set();
  classStudents.forEach(s => {
    Object.keys(gradeIndex[s.id] ?? {}).forEach(sub => subjectSet.add(sub));
  });
  const subjects = [...subjectSet].sort();

  // sort by avg descending
  const sorted = [...classStudents].sort((a, b) => {
    const avgA = parseFloat(getAvg(gradeIndex[a.id] ?? {})) || 0;
    const avgB = parseFloat(getAvg(gradeIndex[b.id] ?? {})) || 0;
    return avgB - avgA;
  });

  const classAvg = sorted.length
    ? (sorted.reduce((sum, s) => sum + (parseFloat(getAvg(gradeIndex[s.id] ?? {})) || 0), 0) / sorted.length).toFixed(1)
    : '—';

  const topScore = sorted[0] ? (getAvg(gradeIndex[sorted[0].id] ?? {}) ?? '—') : '—';
  const below10  = sorted.filter(s => (parseFloat(getAvg(gradeIndex[s.id] ?? {})) || 0) < 10).length;
  const isOpen   = index === 0 ? 'open' : '';

  const subjectHeaders = subjects.map(s => `<th>${s.charAt(0).toUpperCase() + s.slice(1)}</th>`).join('');
  const rows = sorted.length
    ? sorted.map((s, i) => renderStudentRow(s, gradeIndex[s.id] ?? {}, subjects, i + 1)).join('')
    : `<tr><td colspan="${subjects.length + 5}" class="empty-state">No students or grades yet.</td></tr>`;

  return `
    <div class="accordion-card ${isOpen}" data-acc="g-${cls.id}">
      <div class="accordion-trigger" onclick="toggleGrades('g-${cls.id}')">
        <div class="acc-color" style="background:${cls.color}"></div>
        <div class="acc-info">
          <div class="acc-name">${cls.name}</div>
          <div class="acc-meta">${classStudents.length} students · ${cls.period ?? ''} · ${cls.room ?? ''}</div>
        </div>
        <div class="acc-stats">
          <div class="acc-stat">
            <div class="acc-stat-value ${avgClass(classAvg)}">${classAvg}</div>
            <div class="acc-stat-label">Class Avg</div>
          </div>
          <div class="acc-stat">
            <div class="acc-stat-value" style="color:var(--green-mid)">${topScore}</div>
            <div class="acc-stat-label">Top Score</div>
          </div>
          <div class="acc-stat">
            <div class="acc-stat-value" style="${below10 > 0 ? 'color:var(--warn)' : ''}">${below10}</div>
            <div class="acc-stat-label">Below 10</div>
          </div>
        </div>
        <span class="acc-chevron">▼</span>
      </div>
      <div class="accordion-body">
        <table class="student-table">
          <thead><tr><th>#</th><th>Student</th>${subjectHeaders}<th>Average</th><th>Behavior</th><th>Notes</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

// ─── Main Render ─────────────────────────────

export async function renderGrades(appEl) {
  const main = renderPageShell(appEl, 'grades',
    '📊 <span>Grades</span> Overview',
    'Loading grades...',
    renderSidebar
  );

  try {
    const [classesRes, studentsRes, gradesRes] = await Promise.all([
      api.classes.getAll(),
      api.students.getAll(),
      api.grades.get(),
    ]);

    const classes  = classesRes.classes   ?? [];
    const students = studentsRes.students  ?? [];
    const grades   = gradesRes.grades      ?? [];

    const gradeIndex = indexGrades(grades);

    const accordions = classes.map((cls, i) =>
      renderClassBlock(cls, students, gradeIndex, i)
    ).join('');

    main.innerHTML = `
      <div class="page-header">
        <div>
          <div class="page-title">📊 <span>Grades</span> Overview</div>
          <div class="page-subtitle">Ranked by average · All subjects · Click to expand</div>
        </div>
        <div class="header-actions">
          <button class="btn btn-outline" id="exportGradesBtn">📄 Export</button>
          <button class="btn btn-primary" id="reportCardBtn">📝 Generate Report Cards</button>
        </div>
      </div>
      ${renderVoiceBar()}
      <div class="class-accordion">${accordions}</div>
    `;

    window.toggleGrades = id => document.querySelector(`[data-acc="${id}"]`)?.classList.toggle('open');
    initVoiceBar({ onSubmit: text => console.log('[Grades] Voice:', text) });
    document.getElementById('exportGradesBtn')?.addEventListener('click', () => console.log('[Grades] Export'));
    document.getElementById('reportCardBtn')?.addEventListener('click', () => window.navigateTo('reports'));

  } catch (err) {
    console.error('[Grades] Error:', err.message);
    main.innerHTML = renderPageError(err.message, 'grades');
  }
}