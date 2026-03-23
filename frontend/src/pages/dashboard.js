// =============================================
// DIGI-SCHOOL AI — Dashboard Page
// Fetches all data from real API
// =============================================

import '../styles/dashboard.css';

import { getUser }                                                       from '../auth.js';
import { api }                                                           from '../api.js';
import { renderSidebar }                                                 from '../components/sidebar.js';
import { renderVoiceBar, initVoiceBar }                                  from '../components/voiceBar.js';
import { renderStatsGrid }                                               from '../components/statsGrid.js';
import { renderAgentBar, renderAgentLogCard, initAgentBar }             from '../components/agentLog.js';
import { renderFlaggedCard, renderClassesCard, renderAbsenteesCard }    from '../components/flaggedStudents.js';

// ─── Helpers ────────────────────────────────

function getToday() {
  return new Date().toLocaleDateString('en-GB', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  });
}

function getGreetingTime() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}

function todayISO() {
  return new Date().toISOString().split('T')[0];
}

// ─── Loading skeleton ────────────────────────

function renderSkeleton() {
  return `
    <div class="skeleton-header">
      <div class="skeleton-line w60"></div>
      <div class="skeleton-line w30" style="margin-top:8px"></div>
    </div>
    <div class="stats-grid">
      ${[1,2,3,4].map(() => `
        <div class="stat-card">
          <div class="skeleton-line w40"></div>
          <div class="skeleton-line w60" style="height:36px;margin:12px 0 8px"></div>
          <div class="skeleton-line w80"></div>
        </div>
      `).join('')}
    </div>
    <div class="two-col">
      <div class="card" style="height:240px"><div class="skeleton-body"></div></div>
      <div class="card" style="height:240px"><div class="skeleton-body"></div></div>
    </div>
    <div class="two-col">
      <div class="card" style="height:220px"><div class="skeleton-body"></div></div>
      <div class="card" style="height:220px"><div class="skeleton-body"></div></div>
    </div>
    <style>
      .skeleton-header { margin-bottom: 8px; animation: fadeUp 0.3s ease both; }
      .skeleton-line {
        height: 16px;
        border-radius: 8px;
        background: linear-gradient(90deg, var(--green-pale) 25%, #eafbf0 50%, var(--green-pale) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.4s infinite;
        margin-bottom: 6px;
      }
      .skeleton-body {
        margin: 20px;
        height: 80%;
        border-radius: 10px;
        background: linear-gradient(90deg, var(--green-pale) 25%, #eafbf0 50%, var(--green-pale) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.4s infinite;
      }
      .w30 { width: 30%; }
      .w40 { width: 40%; }
      .w60 { width: 60%; }
      .w80 { width: 80%; }
      @keyframes shimmer {
        0%   { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }
    </style>
  `;
}

// ─── Header ─────────────────────────────────

function renderHeader(user) {
  const firstName = (user?.name ?? 'Teacher').split(' ')[0];
  return `
    <div class="main-header">
      <div>
        <div class="greeting">${getGreetingTime()}, <span>${firstName}</span> 👋</div>
        <div class="date-chip">${getToday()}</div>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" id="exportBtn">📄 Export Report</button>
        <button class="btn btn-primary"  id="voiceNoteBtn">🎙️ Voice Note</button>
      </div>
    </div>
  `;
}

// ─── Populate with real data ─────────────────

function populateDashboard(main, { classes, flagged, absentees, voiceHistory, stats }) {
  main.innerHTML = `
    ${renderHeader(getUser())}
    ${renderAgentBar(voiceHistory[0] ?? null)}
    ${renderVoiceBar()}
    ${renderStatsGrid(stats)}

    <div class="two-col">
      ${renderClassesCard(classes)}
      ${renderFlaggedCard(flagged)}
    </div>

    <div class="two-col">
      ${renderAgentLogCard(voiceHistory)}
      ${renderAbsenteesCard(absentees)}
    </div>
  `;

  // ── Listeners ──
  initVoiceBar({
    onSubmit: (text) => {
      console.log('[Dashboard] Voice input:', text);
      // TODO: send to agent pipeline
    },
  });

  initAgentBar({
    onApprove: () => console.log('[Dashboard] Approved'),
    onReview:  () => window.navigateTo('voice'),
  });

  document.getElementById('exportBtn')?.addEventListener('click', () => {
    console.log('[Dashboard] Export triggered');
  });

  document.getElementById('voiceNoteBtn')?.addEventListener('click', () => {
    document.getElementById('micBtn')?.click();
  });
}

// ─── Main Render ─────────────────────────────

export async function renderDashboard(appEl) {
  const user = getUser();

  // 1 — render shell immediately (sidebar + skeleton main)
  appEl.innerHTML = `
    <div class="bg-layer"></div>
    <div class="bg-globe"></div>
    <div class="layout">
      ${renderSidebar('dashboard')}
      <main class="main-content" id="dashMain">
        ${renderSkeleton()}
      </main>
    </div>
  `;

  const main = document.getElementById('dashMain');

  // 2 — fetch all data in parallel
  try {
    const today = todayISO();

    const [classesRes, flaggedRes, attendanceRes, voiceRes] = await Promise.all([
      api.classes.getAll(),
      api.flagged.getAll(),
      api.attendance.today(),
      api.voice.getAll(),
    ]);

    const classes      = classesRes.classes      ?? [];
    const flagged      = flaggedRes.flagged       ?? [];
    const allAtt       = attendanceRes.attendance ?? [];
    const voiceHistory = voiceRes.history         ?? [];

    // absentees = attendance records where status is A, L, or E — today
    const absentees = allAtt.filter(a => ['A','L','E'].includes(a.status));

    // compute stats from real data
    const totalStudents = classes.reduce((s, c) => s + (c.total_students ?? 0), 0);
    const presentToday  = classes.reduce((s, c) => s + (c.present_today  ?? 0), 0);
    const absentToday   = absentees.filter(a => a.status === 'A').length;

    const stats = {
      totalStudents,
      presentToday,
      absentToday,
      flaggedCount: flagged.length,
      classCount:   classes.length,
    };

    // 3 — replace skeleton with real content
    populateDashboard(main, { classes, flagged, absentees, voiceHistory, stats });

  } catch (err) {
    console.error('[Dashboard] Failed to load data:', err.message);
    main.innerHTML = `
      <div style="padding:40px;text-align:center;color:var(--warn)">
        <div style="font-size:32px;margin-bottom:12px">⚠️</div>
        <div style="font-size:15px;font-weight:600">Could not load dashboard data</div>
        <div style="font-size:13px;color:var(--text-light);margin-top:6px">${err.message}</div>
        <button class="btn btn-primary" style="margin-top:20px" onclick="navigateTo('dashboard')">
          Retry
        </button>
      </div>
    `;
  }
}