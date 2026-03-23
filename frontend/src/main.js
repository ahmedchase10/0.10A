// =============================================
// DIGI-SCHOOL AI — Entry Point & Router
// =============================================

import './styles/main.css';
import { isLoggedIn }            from './auth.js';
import { renderAuth }            from './pages/auth.js';
import { renderDashboard }       from './pages/dashboard.js';
import { renderAttendance }      from './pages/attendance.js';
import { renderGrades }          from './pages/grades.js';
import { renderFlagged }         from './pages/flagged.js';
import { renderNotifications }   from './pages/notifications.js';
import { renderStudents }        from './pages/students.js';
import { renderLessons }         from './pages/lessons.js';
import { renderReports }         from './pages/reports.js';
import { renderHomework }        from './pages/homework.js';
import { renderVoiceHistoryPage } from './pages/voiceHistory.js';
import { renderSettings }        from './pages/settings.js';

const app = document.getElementById('app');

const routes = {
  dashboard:     () => renderDashboard(app),
  attendance:    () => renderAttendance(app),
  grades:        () => renderGrades(app),
  flagged:       () => renderFlagged(app),
  notifications: () => renderNotifications(app),
  students:      () => renderStudents(app),
  lessons:       () => renderLessons(app),
  reports:       () => renderReports(app),
  homework:      () => renderHomework(app),
  voice:         () => renderVoiceHistoryPage(app),
  settings:      () => renderSettings(app),
};

function navigate(page) {
  // ── Auth guard ──
  if (!isLoggedIn()) {
    renderAuth(app, () => navigate('dashboard'));
    window.location.hash = 'login';
    return;
  }

  const render = routes[page] || routes['dashboard'];
  render();
  window.location.hash = page;
}

// expose globally so sidebar onclick works
window.navigateTo = navigate;

// on load — check auth first
function init() {
  if (!isLoggedIn()) {
    renderAuth(app, () => navigate('dashboard'));
    return;
  }
  const page = window.location.hash.replace('#', '') || 'dashboard';
  navigate(page);
}

window.addEventListener('hashchange', () => {
  const page = window.location.hash.replace('#', '');
  if (page === 'login') return;
  if (routes[page]) navigate(page);
});

init();