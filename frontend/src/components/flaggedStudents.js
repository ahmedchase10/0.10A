// =============================================
// COMPONENT: Flagged Students, Classes, Absentees
// Accepts live data as parameters — no mockData import
// =============================================

const tagClass = {
  behavior: 'tag-behavior',
  absence:  'tag-absence',
  grade:    'tag-grade',
};

const tagLabel = {
  behavior: 'Behavior',
  absence:  'Absence',
  grade:    'Grades',
};

const dotColor = {
  behavior: '#e76f51',
  absence:  '#e67e22',
  grade:    '#d4a017',
};

const statusLabel = {
  absent:  'Absent',
  excused: 'Excused',
  late:    'Late',
};

// ─── Flagged Students Card ──────────────────

export function renderFlaggedCard(flagged = []) {
  const items = flagged.length
    ? flagged.map(s => `
        <div class="flag-item">
          <div class="flag-dot" style="background:${dotColor[s.type] ?? '#aaa'}"></div>
          <div class="flag-body">
            <div class="flag-name">${s.student_name} — ${s.class_name}</div>
            <div class="flag-reason">${s.reason}</div>
          </div>
          <span class="flag-tag ${tagClass[s.type]}">${tagLabel[s.type]}</span>
        </div>
      `).join('')
    : `<div class="empty-state" style="padding:20px;text-align:center;color:var(--text-light);font-size:13px;">No flagged students 🎉</div>`;

  return `
    <div class="card">
      <div class="card-header">
        <div class="card-title">Flagged Students</div>
        <span class="card-action" onclick="navigateTo('flagged')" style="cursor:pointer">View all →</span>
      </div>
      <div class="flagged-list">${items}</div>
    </div>
  `;
}

// ─── Classes Card ───────────────────────────

export function renderClassesCard(classes = []) {
  const rows = classes.length
    ? classes.map(cls => {
        const total   = cls.total_students ?? 0;
        const present = cls.present_today  ?? 0;
        const pct     = total > 0 ? Math.round((present / total) * 100) : 0;
        return `
          <div class="class-row">
            <div class="class-color" style="background:${cls.color}"></div>
            <div class="class-info">
              <div class="class-name">${cls.name}</div>
              <div class="class-meta">${total} students · ${cls.period ?? ''} · ${cls.room ?? ''}</div>
            </div>
            <div class="class-att">
              <div class="att-num">${present}/${total}</div>
              <div class="att-label">present</div>
              <div class="att-bar-wrap">
                <div class="att-bar" style="width:${pct}%"></div>
              </div>
            </div>
          </div>
        `;
      }).join('')
    : `<div class="empty-state" style="padding:20px;text-align:center;color:var(--text-light);font-size:13px;">No classes yet. Add one in Settings.</div>`;

  return `
    <div class="card">
      <div class="card-header">
        <div class="card-title">My Classes</div>
        <span class="card-action" onclick="navigateTo('attendance')" style="cursor:pointer">See all →</span>
      </div>
      <div class="class-list">${rows}</div>
    </div>
  `;
}

// ─── Absentees Card ─────────────────────────

export function renderAbsenteesCard(absentees = []) {
  const rows = absentees.length
    ? absentees.map(s => {
        const status = s.status === 'A' ? 'absent'
                     : s.status === 'E' ? 'excused'
                     : s.status === 'L' ? 'late'
                     : 'absent';
        return `
          <div class="att-row">
            <div>
              <div class="student-name">${s.student_name}</div>
              <div class="student-class">${s.class_name}</div>
            </div>
            <span class="status-chip status-${status}">${statusLabel[status] ?? status}</span>
          </div>
        `;
      }).join('')
    : `<div class="empty-state" style="padding:20px;text-align:center;color:var(--text-light);font-size:13px;">No absences today 🎉</div>`;

  return `
    <div class="card">
      <div class="card-header">
        <div class="card-title">Today's Absentees</div>
        <span class="card-action" onclick="navigateTo('notifications')" style="cursor:pointer">Notify parents →</span>
      </div>
      <div class="att-quick">${rows}</div>
    </div>
  `;
}