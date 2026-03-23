// =============================================
// DIGI-SCHOOL AI — Voice History (Live Data)
// =============================================

import '../styles/pages.css';
import { renderSidebar } from '../components/sidebar.js';
import { api }           from '../api.js';
import { renderPageShell, renderPageError } from '../utils/pageUtils.js';

function renderAction(action) {
  const label = typeof action === 'string' ? action : action.label ?? JSON.stringify(action);
  const icon  = typeof action === 'object' && action.icon ? action.icon : '•';
  return `<div class="vh-action"><span class="vh-action-icon">${icon}</span><span class="vh-action-label">${label}</span></div>`;
}

function renderVoiceCard(entry) {
  const actions = Array.isArray(entry.actions_json) ? entry.actions_json : [];
  const time    = new Date(entry.recorded_at).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'});
  const date    = new Date(entry.recorded_at).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'});
  const dur     = entry.duration_sec ? `${entry.duration_sec}s` : '—';

  return `
    <div class="vh-card">
      <div class="vh-card-top">
        <div class="vh-card-left">
          <div class="vh-mic-icon">🎙️</div>
          <div>
            <div class="vh-meta-row">
              <span class="vh-date">${date} · ${time}</span>
              <span class="vh-duration">⏱ ${dur}</span>
            </div>
            <div class="vh-class-chip" style="background:${entry.color ?? '#40916c'}22;color:${entry.color ?? '#40916c'};border:1px solid ${entry.color ?? '#40916c'}44">
              ${entry.class_name ?? 'Unknown class'}
            </div>
          </div>
        </div>
        <span class="vh-count-chip">${entry.actions_count ?? actions.length} action${(entry.actions_count ?? actions.length) !== 1 ? 's' : ''}</span>
      </div>
      <div class="vh-transcript">
        <span class="vh-transcript-label">Transcript</span>
        <p class="vh-transcript-text">"${entry.transcript}"</p>
      </div>
      ${actions.length ? `
        <div class="vh-divider"></div>
        <div class="vh-actions-label">Agent executed</div>
        <div class="vh-actions-list">${actions.map(renderAction).join('')}</div>
      ` : ''}
    </div>
  `;
}

export async function renderVoiceHistoryPage(appEl) {
  const main = renderPageShell(appEl, 'voice', '🎙️ <span>Voice</span> History', 'Loading...', renderSidebar);

  try {
    const [voiceRes, classesRes] = await Promise.all([
      api.voice.getAll(),
      api.classes.getAll(),
    ]);

    const history = voiceRes.history   ?? [];
    const classes = classesRes.classes ?? [];
    const totalActions = history.reduce((s, v) => s + (v.actions_count ?? 0), 0);

    const classOptions = classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

    main.innerHTML = `
      <div class="page-header">
        <div>
          <div class="page-title">🎙️ <span>Voice</span> History</div>
          <div class="page-subtitle">${history.length} recordings · ${totalActions} total actions executed</div>
        </div>
        <div class="header-actions"><button class="btn btn-outline">📄 Export Log</button></div>
      </div>

      <div class="vh-filter-bar">
        <div class="vh-search-wrap">
          <span class="vh-search-icon">🔍</span>
          <input class="vh-search" id="vhSearch" type="text" placeholder="Search transcripts..." />
        </div>
        <select class="vh-filter-select" id="vhClassFilter">
          <option value="">All classes</option>
          ${classOptions}
        </select>
      </div>

      <div class="vh-cards-list" id="vhList">
        ${history.length ? history.map(renderVoiceCard).join('') : '<div class="empty-state" style="padding:60px;text-align:center;color:var(--text-light)">No voice notes recorded yet.</div>'}
      </div>

      <style>
        .vh-filter-bar { display:flex; gap:12px; align-items:center; animation:fadeUp 0.4s ease 0.05s both; }
        .vh-search-wrap { flex:1; display:flex; align-items:center; gap:10px; background:white; border:1.5px solid var(--green-pale); border-radius:50px; padding:10px 18px; box-shadow:var(--card-shadow); transition:border-color 0.2s; }
        .vh-search-wrap:focus-within { border-color:var(--green-light); }
        .vh-search { flex:1; font-size:13px; color:var(--text-dark); background:transparent; border:none; outline:none; font-family:var(--font-body); }
        .vh-search::placeholder { color:var(--text-light); }
        .vh-filter-select { background:white; border:1.5px solid var(--green-pale); border-radius:50px; padding:10px 18px; font-size:13px; font-family:var(--font-body); color:var(--text-dark); cursor:pointer; box-shadow:var(--card-shadow); outline:none; }
        .vh-cards-list { display:flex; flex-direction:column; gap:16px; animation:fadeUp 0.4s ease 0.1s both; }
        .vh-card { background:white; border-radius:var(--radius); box-shadow:var(--card-shadow); padding:22px; display:flex; flex-direction:column; gap:14px; border:1.5px solid transparent; transition:border-color 0.2s,transform 0.18s; }
        .vh-card:hover { border-color:var(--green-pale); transform:translateY(-2px); }
        .vh-card-top { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
        .vh-card-left { display:flex; align-items:center; gap:14px; }
        .vh-mic-icon { width:42px; height:42px; background:linear-gradient(135deg,var(--green-mid),var(--green-deep)); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; box-shadow:0 4px 12px rgba(64,145,108,0.30); }
        .vh-meta-row { display:flex; align-items:center; gap:10px; margin-bottom:6px; }
        .vh-date { font-size:13px; font-weight:600; color:var(--text-dark); }
        .vh-duration { font-size:11px; color:var(--text-light); background:var(--cream); padding:2px 8px; border-radius:20px; border:1px solid var(--green-pale); }
        .vh-class-chip { display:inline-block; font-size:11px; font-weight:600; padding:3px 10px; border-radius:20px; }
        .vh-count-chip { background:var(--green-pale); color:var(--green-deep); font-size:11px; font-weight:700; padding:4px 12px; border-radius:20px; white-space:nowrap; flex-shrink:0; }
        .vh-transcript { background:var(--cream); border-radius:var(--radius-sm); padding:14px 16px; border-left:3px solid var(--green-light); }
        .vh-transcript-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-light); display:block; margin-bottom:6px; }
        .vh-transcript-text { font-size:13px; color:var(--text-dark); line-height:1.6; font-style:italic; }
        .vh-divider { height:1px; background:var(--green-pale); }
        .vh-actions-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-light); }
        .vh-actions-list { display:flex; flex-wrap:wrap; gap:8px; }
        .vh-action { display:flex; align-items:center; gap:6px; background:var(--green-pale); border-radius:20px; padding:5px 12px; font-size:12px; color:var(--green-deep); font-weight:500; }
      </style>
    `;

    // live search + filter
    const searchEl = document.getElementById('vhSearch');
    const filterEl = document.getElementById('vhClassFilter');
    const listEl   = document.getElementById('vhList');

    function applyFilter() {
      const q  = searchEl.value.toLowerCase().trim();
      const cId = filterEl.value ? parseInt(filterEl.value) : null;
      const filtered = history.filter(e => {
        const matchClass  = !cId || e.class_id === cId;
        const matchSearch = !q || e.transcript.toLowerCase().includes(q) || (e.class_name ?? '').toLowerCase().includes(q);
        return matchClass && matchSearch;
      });
      listEl.innerHTML = filtered.length
        ? filtered.map(renderVoiceCard).join('')
        : '<div class="empty-state" style="padding:40px;text-align:center;color:var(--text-light)">No results found.</div>';
    }

    searchEl?.addEventListener('input', applyFilter);
    filterEl?.addEventListener('change', applyFilter);

  } catch (err) {
    console.error('[VoiceHistory] Error:', err.message);
    main.innerHTML = renderPageError(err.message, 'voice');
  }
}