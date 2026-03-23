// =============================================
// DIGI-SCHOOL AI — Report Cards (Live Data)
// =============================================

import '../styles/pages.css';
import { renderSidebar } from '../components/sidebar.js';
import { api }           from '../api.js';
import { renderPageShell, renderPageError } from '../utils/pageUtils.js';

function getAvg(gradeMap) {
  const vals = Object.values(gradeMap ?? {});
  if (!vals.length) return null;
  return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
}

function avgClass(avg) {
  const n = parseFloat(avg);
  if (n >= 16) return 'grade-high';
  if (n >= 12) return 'grade-mid';
  return 'grade-low';
}

function generateText(student, gradeMap, absentCount) {
  const avg  = parseFloat(getAvg(gradeMap)) || 0;
  const name = student.name.split(' ')[0];

  const perf = avg >= 16
    ? `${name} has demonstrated outstanding academic performance this semester, consistently achieving high marks across all subjects.`
    : avg >= 12
    ? `${name} has shown satisfactory progress this semester, performing at a good level across most subjects.`
    : `${name} has encountered some difficulties this semester and would benefit from additional support in key areas.`;

  const att = absentCount === 0
    ? `Attendance has been excellent with no recorded absences.`
    : absentCount <= 2
    ? `Attendance has been generally consistent, with ${absentCount} absence(s) recorded.`
    : `Attendance requires improvement, with ${absentCount} absences recorded this period.`;

  const beh = student.behavior === 'Excellent'
    ? `Behaviour in class has been exemplary — ${name} is a positive presence and actively participates.`
    : student.behavior === 'Good'
    ? `${name} maintains good conduct and engages constructively during lessons.`
    : `Some behavioural concerns have been noted and will require continued monitoring.`;

  const close = avg >= 16 ? `We encourage ${name} to maintain this excellent standard.`
    : avg >= 12 ? `We encourage ${name} to continue building on this solid foundation.`
    : `We recommend targeted revision and close collaboration between school and family.`;

  return `${perf} ${att} ${beh} ${close}`;
}

function renderReportCard(student, gradeMap, absentCount) {
  const avg      = getAvg(gradeMap);
  const avgCls   = avgClass(avg);
  const behavKey = (student.behavior ?? 'Good').replace(/\s+/g, '-');
  const text     = generateText(student, gradeMap, absentCount);

  return `
    <div class="report-card" id="rc-${student.id}">
      <div class="report-card-header">
        <div class="report-card-who">
          <div class="rc-avatar">${student.name.charAt(0)}</div>
          <div>
            <div class="rc-name">${student.name}</div>
            <div class="rc-meta">
              <span class="avg-badge ${avgCls}">Avg: ${avg ?? '—'}/20</span>
              <span class="behavior-badge behavior-${behavKey}">${student.behavior ?? 'Good'}</span>
              ${absentCount ? `<span class="att-chip A">${absentCount} absent</span>` : ''}
            </div>
          </div>
        </div>
        <div id="rc-status-${student.id}">
          <span class="rc-status-chip pending">⏳ Pending</span>
        </div>
      </div>
      <textarea class="rc-textarea" id="rc-text-${student.id}" rows="4">${text}</textarea>
      <div class="rc-actions">
        <button class="btn btn-outline rc-btn" onclick="approveCard('${student.id}')">✓ Approve</button>
        <button class="btn btn-outline rc-btn" style="font-size:12px">🔄 Regenerate</button>
      </div>
    </div>
  `;
}

function renderClassBlock(cls, students, gradeIndex, attIndex, index) {
  const classStudents = students.filter(s => s.class_id === cls.id);
  const isOpen = index === 0 ? 'open' : '';
  const cards  = classStudents.map(s =>
    renderReportCard(s, gradeIndex[s.id] ?? {}, (attIndex[s.id] ?? []).filter(r => r.status === 'A').length)
  ).join('');

  return `
    <div class="accordion-card ${isOpen}" data-acc="rc-${cls.id}">
      <div class="accordion-trigger" onclick="toggleRc('rc-${cls.id}')">
        <div class="acc-color" style="background:${cls.color}"></div>
        <div class="acc-info">
          <div class="acc-name">${cls.name}</div>
          <div class="acc-meta">${classStudents.length} students · ${cls.period ?? ''}</div>
        </div>
        <div class="acc-stats">
          <div class="acc-stat"><div class="acc-stat-value">${classStudents.length}</div><div class="acc-stat-label">Cards</div></div>
          <div class="acc-stat"><div class="acc-stat-value" id="app-count-${cls.id}" style="color:var(--green-mid)">0</div><div class="acc-stat-label">Approved</div></div>
        </div>
        <span class="acc-chevron">▼</span>
      </div>
      <div class="accordion-body">
        <div class="rc-class-actions">
          <button class="btn btn-primary" style="font-size:12px" onclick="approveAll('${cls.id}')">✓ Approve All</button>
          <button class="btn btn-outline" style="font-size:12px">📄 Export PDF</button>
        </div>
        <div class="rc-cards-grid">${cards || '<div class="empty-state" style="padding:30px">No students yet.</div>'}</div>
      </div>
    </div>
  `;
}

export async function renderReports(appEl) {
  const main = renderPageShell(appEl, 'reports', '📝 <span>Report</span> Cards', 'Loading...', renderSidebar);

  try {
    const [classesRes, studentsRes, gradesRes, attRes] = await Promise.all([
      api.classes.getAll(),
      api.students.getAll(),
      api.grades.get(),
      api.attendance.today(),
    ]);

    const classes  = classesRes.classes   ?? [];
    const students = studentsRes.students  ?? [];
    const grades   = gradesRes.grades      ?? [];
    const att      = attRes.attendance     ?? [];

    const gradeIndex = {};
    grades.forEach(g => {
      if (!gradeIndex[g.student_id]) gradeIndex[g.student_id] = {};
      gradeIndex[g.student_id][g.subject] = parseFloat(g.score);
    });

    const attIndex = {};
    att.forEach(r => {
      if (!attIndex[r.student_id]) attIndex[r.student_id] = [];
      attIndex[r.student_id].push(r);
    });

    const accordions = classes.map((cls, i) =>
      renderClassBlock(cls, students, gradeIndex, attIndex, i)
    ).join('');

    main.innerHTML = `
      <div class="page-header">
        <div>
          <div class="page-title">📝 <span>Report</span> Cards</div>
          <div class="page-subtitle">${students.length} AI-generated reports · Review, edit and approve</div>
        </div>
        <div class="header-actions">
          <button class="btn btn-outline">📄 Export All</button>
          <button class="btn btn-primary" onclick="approveAllClasses()">✓ Approve All</button>
        </div>
      </div>
      <div class="class-accordion">${accordions}</div>
      <style>
        .rc-class-actions { display:flex; gap:10px; padding:14px 22px; border-bottom:1px solid var(--green-pale); background:var(--cream); }
        .rc-cards-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(380px,1fr)); gap:16px; padding:20px; }
        .report-card { background:white; border-radius:var(--radius); border:1.5px solid var(--green-pale); box-shadow:var(--card-shadow); padding:18px; display:flex; flex-direction:column; gap:12px; transition:border-color 0.2s; }
        .report-card.approved { border-color:var(--green-light); }
        .report-card-header { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
        .report-card-who { display:flex; align-items:center; gap:10px; }
        .rc-avatar { width:34px; height:34px; border-radius:50%; background:linear-gradient(135deg,var(--green-mid),var(--green-deep)); color:white; font-weight:700; font-size:13px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .rc-name { font-size:14px; font-weight:600; color:var(--text-dark); }
        .rc-meta { display:flex; gap:6px; flex-wrap:wrap; margin-top:4px; align-items:center; }
        .avg-badge { font-size:11px; font-weight:700; padding:2px 8px; border-radius:20px; }
        .avg-badge.grade-high { background:var(--green-pale); color:var(--green-deep); }
        .avg-badge.grade-mid  { background:#eaf4ff; color:#2980b9; }
        .avg-badge.grade-low  { background:#fdebd0; color:var(--warn); }
        .rc-status-chip { font-size:11px; font-weight:600; padding:3px 10px; border-radius:20px; white-space:nowrap; }
        .rc-status-chip.pending  { background:#fdebd0; color:var(--warn); }
        .rc-status-chip.approved { background:var(--green-pale); color:var(--green-mid); }
        .rc-textarea { width:100%; border:1.5px solid var(--green-pale); border-radius:var(--radius-sm); padding:12px 14px; font-family:var(--font-body); font-size:13px; color:var(--text-dark); resize:vertical; line-height:1.6; background:var(--cream); transition:border-color 0.2s; }
        .rc-textarea:focus { outline:none; border-color:var(--green-light); background:white; }
        .rc-actions { display:flex; gap:8px; }
        .rc-btn { flex:1; justify-content:center; font-size:12px; padding:7px 12px; }
      </style>
    `;

    window.toggleRc = id => document.querySelector(`[data-acc="${id}"]`)?.classList.toggle('open');

    window.approveCard = (studentId) => {
      const card   = document.getElementById(`rc-${studentId}`);
      const status = document.getElementById(`rc-status-${studentId}`);
      if (card) card.classList.add('approved');
      if (status) status.innerHTML = '<span class="rc-status-chip approved">✓ Approved</span>';
    };

    window.approveAll = (classId) => {
      const classStudents = students.filter(s => s.class_id === parseInt(classId));
      classStudents.forEach(s => window.approveCard(s.id));
      const countEl = document.getElementById(`app-count-${classId}`);
      if (countEl) countEl.textContent = classStudents.length;
    };

    window.approveAllClasses = () => classes.forEach(cls => window.approveAll(cls.id));

  } catch (err) {
    console.error('[Reports] Error:', err.message);
    main.innerHTML = renderPageError(err.message, 'reports');
  }
}