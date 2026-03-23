// =============================================
// DIGI-SCHOOL AI — Settings Page (Live Data)
// =============================================

import '../styles/pages.css';
import { renderSidebar } from '../components/sidebar.js';
import { api }           from '../api.js';
import { getUser, setSession, getToken } from '../auth.js';
import { renderPageShell, renderPageError } from '../utils/pageUtils.js';

function section(title, subtitle, content) {
  return `
    <div class="settings-section">
      <div class="settings-section-header">
        <div class="settings-section-title">${title}</div>
        <div class="settings-section-sub">${subtitle}</div>
      </div>
      <div class="settings-section-body">${content}</div>
    </div>
  `;
}

function textRow(label, hint, id, value) {
  return `
    <div class="settings-row">
      <div class="settings-row-left">
        <div class="settings-row-label">${label}</div>
        <div class="settings-row-hint">${hint}</div>
      </div>
      <input class="settings-input" id="${id}" type="text" value="${value ?? ''}" />
    </div>
  `;
}

function toggleRow(label, hint, id, checked = true) {
  return `
    <div class="settings-row">
      <div class="settings-row-left">
        <div class="settings-row-label">${label}</div>
        <div class="settings-row-hint">${hint}</div>
      </div>
      <label class="toggle-switch">
        <input type="checkbox" id="${id}" ${checked ? 'checked' : ''} />
        <span class="toggle-track"></span>
      </label>
    </div>
  `;
}

function selectRow(label, hint, id, options, selected) {
  const opts = options.map(o => `<option value="${o.value}" ${o.value === selected ? 'selected' : ''}>${o.label}</option>`).join('');
  return `
    <div class="settings-row">
      <div class="settings-row-left">
        <div class="settings-row-label">${label}</div>
        <div class="settings-row-hint">${hint}</div>
      </div>
      <select class="settings-select" id="${id}">${opts}</select>
    </div>
  `;
}

function dangerRow(label, hint, btnLabel, btnId) {
  return `
    <div class="settings-row danger-row">
      <div class="settings-row-left">
        <div class="settings-row-label" style="color:var(--warn)">${label}</div>
        <div class="settings-row-hint">${hint}</div>
      </div>
      <button class="btn-danger" id="${btnId}">${btnLabel}</button>
    </div>
  `;
}

export async function renderSettings(appEl) {
  const main = renderPageShell(appEl, 'settings', '⚙️ <span>Settings</span>', 'Loading your profile...', renderSidebar);

  try {
    // fetch live teacher profile
    const { teacher } = await api.auth.me();

    main.innerHTML = `
      <div class="page-header">
        <div>
          <div class="page-title">⚙️ <span>Settings</span></div>
          <div class="page-subtitle">Manage your profile, agent behaviour, and preferences</div>
        </div>
        <div class="header-actions">
          <button class="btn btn-outline" id="cancelBtn">Cancel</button>
          <button class="btn btn-primary" id="saveBtn">💾 Save Changes</button>
        </div>
      </div>

      <div class="settings-body">
        ${section('👤 Teacher Profile', 'Your personal information shown across the platform', `
          ${textRow('Full Name',  'Displayed in the sidebar and reports',           'set-name',    teacher.name)}
          ${textRow('Subject',    'Main subject you teach',                         'set-subject', teacher.subject)}
          ${textRow('School',     'Your school name (used in report cards)',        'set-school',  teacher.school)}
          ${textRow('Email',      'Your account email',                            'set-email',   teacher.email)}
        `)}
        ${section('🤖 Agent Behaviour', 'Control what the agent does automatically', `
          ${toggleRow('Auto-mark attendance',     'Detect absent/late students from voice notes',          'set-auto-att',      true)}
          ${toggleRow('Auto-flag students',       'Flag students when thresholds are exceeded',            'set-auto-flag',     true)}
          ${toggleRow('Auto-log lessons',         'Update teaching log from voice notes',                  'set-auto-lesson',   true)}
          ${toggleRow('Auto-log homework',        'Detect homework assignments from voice notes',          'set-auto-hw',       true)}
          ${toggleRow('Auto-draft notifications', 'Prepare parent messages when a student is flagged',     'set-auto-notif',    true)}
          ${toggleRow('Store agent insights',     'Save AI insights for next session planning',            'set-auto-insights', true)}
        `)}
        ${section('🌐 Language & Input', 'Configure how voice input is processed', `
          ${selectRow('Primary language', 'Agent will prioritize this language', 'set-lang', [
            { value:'ar', label:'Arabic (العربية)' },
            { value:'fr', label:'French (Français)' },
            { value:'en', label:'English' },
          ], 'fr')}
          ${toggleRow('Mixed-language support', 'Allow voice notes in multiple languages simultaneously', 'set-multilang', true)}
        `)}
        ${section('🔔 Notification Preferences', 'Control when alerts are triggered', `
          ${toggleRow('Absence threshold alerts', 'Alert when a student exceeds the absence threshold', 'set-notif-abs', true)}
          ${toggleRow('Grade decline alerts',     'Alert when a grade drops significantly',             'set-notif-grade', true)}
          ${toggleRow('Behaviour repeat alerts',  'Alert on 3rd behavioural incident in a week',        'set-notif-beh', true)}
          ${selectRow('Absence threshold', 'Number of absences before triggering a notification', 'set-abs-thresh', [
            { value:'3', label:'3 absences' },
            { value:'4', label:'4 absences' },
            { value:'5', label:'5 absences' },
            { value:'7', label:'7 absences' },
          ], '5')}
        `)}
        ${section('⚠️ Data Management', 'Irreversible actions — proceed with caution', `
          ${dangerRow('Reset agent memory',  'Wipe all stored insights and lesson logs', '🔄 Reset Memory', 'btn-reset')}
          ${dangerRow('Export all data',     'Download a full backup of all data',       '📦 Export Backup', 'btn-export')}
        `)}
      </div>

      <style>
        .settings-body { display:flex; flex-direction:column; gap:20px; animation:fadeUp 0.4s ease 0.05s both; }
        .settings-section { background:white; border-radius:var(--radius); box-shadow:var(--card-shadow); overflow:hidden; }
        .settings-section-header { padding:18px 24px 14px; border-bottom:1px solid var(--green-pale); }
        .settings-section-title { font-family:var(--font-display); font-size:16px; color:var(--text-dark); }
        .settings-section-sub { font-size:12px; color:var(--text-light); margin-top:3px; }
        .settings-section-body { padding:4px 0; }
        .settings-row { display:flex; align-items:center; justify-content:space-between; gap:20px; padding:15px 24px; border-bottom:1px solid var(--green-pale); transition:background 0.12s; }
        .settings-row:last-child { border-bottom:none; }
        .settings-row:hover { background:#f8fefb; }
        .settings-row-left { flex:1; min-width:0; }
        .settings-row-label { font-size:14px; font-weight:500; color:var(--text-dark); }
        .settings-row-hint { font-size:12px; color:var(--text-light); margin-top:2px; }
        .settings-input { border:1.5px solid var(--green-pale); border-radius:var(--radius-sm); padding:8px 14px; font-size:13px; font-family:var(--font-body); color:var(--text-dark); background:var(--cream); width:220px; transition:border-color 0.2s; }
        .settings-input:focus { outline:none; border-color:var(--green-light); background:white; }
        .settings-select { border:1.5px solid var(--green-pale); border-radius:var(--radius-sm); padding:8px 14px; font-size:13px; font-family:var(--font-body); color:var(--text-dark); background:var(--cream); width:220px; cursor:pointer; outline:none; }
        .toggle-switch { position:relative; display:inline-block; width:44px; height:24px; flex-shrink:0; cursor:pointer; }
        .toggle-switch input { display:none; }
        .toggle-track { position:absolute; inset:0; background:#d0e8da; border-radius:99px; transition:background 0.2s; }
        .toggle-track::after { content:''; position:absolute; top:3px; left:3px; width:18px; height:18px; background:white; border-radius:50%; box-shadow:0 1px 4px rgba(0,0,0,0.18); transition:transform 0.2s; }
        .toggle-switch input:checked + .toggle-track { background:var(--green-mid); }
        .toggle-switch input:checked + .toggle-track::after { transform:translateX(20px); }
        .danger-row:hover { background:#fff8f5; }
        .btn-danger { background:white; color:var(--warn); border:1.5px solid #f5c6b8; border-radius:50px; padding:8px 16px; font-size:12px; font-weight:500; font-family:var(--font-body); cursor:pointer; transition:all 0.18s; white-space:nowrap; }
        .btn-danger:hover { background:var(--warn); color:white; border-color:var(--warn); }
        .settings-toast { position:fixed; bottom:28px; right:28px; background:var(--green-deep); color:white; font-size:13px; font-weight:500; padding:12px 22px; border-radius:50px; box-shadow:0 6px 20px rgba(45,106,79,0.35); z-index:999; animation:fadeUp 0.3s ease both; font-family:var(--font-body); }
      </style>
    `;

    // save
    document.getElementById('saveBtn')?.addEventListener('click', async () => {
      // TODO: add a PUT /api/auth/profile endpoint when needed
      // For now update the session with new name/subject
      const name    = document.getElementById('set-name')?.value.trim();
      const subject = document.getElementById('set-subject')?.value.trim();
      const school  = document.getElementById('set-school')?.value.trim();

      const updated = { ...teacher, name, subject, school };
      setSession(updated, getToken());

      const toast = document.createElement('div');
      toast.className = 'settings-toast';
      toast.textContent = '✓ Settings saved successfully';
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 2800);
    });

    document.getElementById('cancelBtn')?.addEventListener('click', () => window.navigateTo('dashboard'));
    document.getElementById('btn-reset')?.addEventListener('click', () => {
      if (confirm('Reset all agent memory? This cannot be undone.')) console.log('[Settings] Memory reset');
    });
    document.getElementById('btn-export')?.addEventListener('click', () => console.log('[Settings] Export triggered'));

  } catch (err) {
    console.error('[Settings] Error:', err.message);
    main.innerHTML = renderPageError(err.message, 'settings');
  }
}