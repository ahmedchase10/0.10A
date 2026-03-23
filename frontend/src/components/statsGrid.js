// =============================================
// COMPONENT: Stats Grid
// Accepts live data as parameter — no mockData import
// =============================================

export function renderStatsGrid(stats) {
  const attendancePct = stats.totalStudents > 0
    ? Math.round((stats.presentToday / stats.totalStudents) * 100)
    : 0;

  const cards = [
    {
      icon:     '👥',
      label:    'Total Students',
      value:    stats.totalStudents,
      sub:      `Across ${stats.classCount ?? '—'} classes`,
      subClass: '',
    },
    {
      icon:     '✅',
      label:    'Present Today',
      value:    stats.presentToday,
      sub:      `↑ ${attendancePct}% attendance rate`,
      subClass: 'trend-up',
    },
    {
      icon:     '⚠️',
      label:    'Absent Today',
      value:    stats.absentToday,
      sub:      'Marked absent or late today',
      subClass: stats.absentToday > 0 ? 'trend-down' : '',
    },
    {
      icon:     '🚩',
      label:    'Flagged Students',
      value:    stats.flaggedCount,
      sub:      stats.flaggedCount > 0 ? 'Needs attention' : 'All clear',
      subClass: stats.flaggedCount > 0 ? 'trend-down' : 'trend-up',
    },
  ];

  return `
    <div class="stats-grid">
      ${cards.map(c => `
        <div class="stat-card">
          <span class="stat-icon">${c.icon}</span>
          <div class="stat-label">${c.label}</div>
          <div class="stat-value">${c.value}</div>
          <div class="stat-sub ${c.subClass}">${c.sub}</div>
        </div>
      `).join('')}
    </div>
  `;
}