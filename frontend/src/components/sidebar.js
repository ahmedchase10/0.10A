// =============================================
// COMPONENT: Sidebar
// Uses live session data — no mockData import
// =============================================

import { getUser } from '../auth.js';
import { logout }  from '../auth.js';

window.handleLogout = () => {
  logout();
  import('../pages/auth.js').then(({ renderAuth }) => {
    const app = document.getElementById('app');
    renderAuth(app, () => window.navigateTo('dashboard'));
  });
  window.location.hash = '';
};

const navItems = [
  { section: 'Overview' },
  { icon: '🏠', label: 'Dashboard',            page: 'dashboard'     },
  { icon: '📋', label: 'Attendance',           page: 'attendance'    },
  { icon: '📊', label: 'Grades',               page: 'grades'        },
  { section: 'Management' },
  { icon: '👥', label: 'Students',             page: 'students'      },
  { icon: '📚', label: 'Lesson Log',           page: 'lessons'       },
  { icon: '📝', label: 'Report Cards',         page: 'reports'       },
  { icon: '🏠', label: 'Homework',             page: 'homework'      },
  { section: 'Alerts' },
  { icon: '🚩', label: 'Flagged Students',     page: 'flagged'       },
  { icon: '📨', label: 'Parent Notifications', page: 'notifications' },
  { section: 'Tools' },
  { icon: '🎙️', label: 'Voice History',       page: 'voice'         },
  { icon: '⚙️',  label: 'Settings',           page: 'settings'      },
];

export function renderSidebar(activePage = 'dashboard') {
  const user = getUser();
  const name     = user?.name     ?? 'Teacher';
  const initials = user?.initials ?? name.split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase();
  const subject  = user?.subject  ?? '';
  const grades   = user?.grades   ?? '';

  const navHTML = navItems.map(item => {
    if (item.section) return `<div class="nav-section">${item.section}</div>`;
    const isActive = item.page === activePage;
    return `
      <div class="nav-item ${isActive ? 'active' : ''}" data-page="${item.page}" onclick="navigateTo('${item.page}')">
        <span class="nav-icon">${item.icon}</span>
        ${item.label}
      </div>
    `;
  }).join('');

  return `
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-icon">🌿</div>
        <div class="logo-text">
          Digi-School AI
          <span>Teacher Portal</span>
        </div>
      </div>

      ${navHTML}

      <div class="teacher-profile">
        <div class="avatar">${initials}</div>
        <div class="teacher-info">
          <div class="teacher-name">M. ${name}</div>
          <div class="teacher-role">${subject}${grades ? ' — ' + grades : ''}</div>
        </div>
        <button onclick="handleLogout()" title="Sign out" style="
          background:none;border:none;cursor:pointer;color:rgba(255,255,255,0.4);
          font-size:15px;padding:4px;transition:color 0.15s;flex-shrink:0;
        " onmouseover="this.style.color='white'" onmouseout="this.style.color='rgba(255,255,255,0.4)'">🚪</button>
      </div>
    </aside>
  `;
}