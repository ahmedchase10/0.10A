// =============================================
// DIGI-SCHOOL AI — Page Utils
// Shared skeleton loader + error state
// =============================================

export function renderPageSkeleton(title, subtitle) {
  return `
    <div class="page-header">
      <div>
        <div class="page-title">${title}</div>
        <div class="page-subtitle">${subtitle}</div>
      </div>
    </div>
    <div class="skeleton-list">
      ${[1,2,3].map(() => `
        <div class="card" style="overflow:hidden">
          <div class="skeleton-row">
            <div class="sk-circle"></div>
            <div style="flex:1">
              <div class="sk-line w50"></div>
              <div class="sk-line w30" style="margin-top:6px"></div>
            </div>
            <div class="sk-line w10"></div>
          </div>
        </div>
      `).join('')}
    </div>
    <style>
      .skeleton-list { display:flex; flex-direction:column; gap:16px; animation: fadeUp 0.3s ease both; }
      .skeleton-row  { display:flex; align-items:center; gap:14px; padding:18px 22px; }
      .sk-circle     { width:42px; height:42px; border-radius:50%; background:var(--green-pale); flex-shrink:0; }
      .sk-line       { height:14px; border-radius:8px; background: linear-gradient(90deg, var(--green-pale) 25%, #eafbf0 50%, var(--green-pale) 75%); background-size:200% 100%; animation: shimmer 1.4s infinite; }
      .w10 { width:10%; } .w30 { width:30%; } .w50 { width:50%; }
      @keyframes shimmer { 0% { background-position:200% 0; } 100% { background-position:-200% 0; } }
    </style>
  `;
}

export function renderPageError(msg, retryPage) {
  return `
    <div style="padding:60px 20px;text-align:center">
      <div style="font-size:36px;margin-bottom:16px">⚠️</div>
      <div style="font-size:16px;font-weight:600;color:var(--text-dark)">Could not load data</div>
      <div style="font-size:13px;color:var(--text-light);margin-top:6px">${msg}</div>
      <button class="btn btn-primary" style="margin-top:20px"
        onclick="navigateTo('${retryPage}')">↺ Retry</button>
    </div>
  `;
}

// Shared page shell — sidebar + main with skeleton, returns main el
export function renderPageShell(appEl, activePage, title, subtitle, sidebarFn) {
  appEl.innerHTML = `
    <div class="bg-layer"></div>
    <div class="bg-globe"></div>
    <div class="layout">
      ${sidebarFn(activePage)}
      <main class="main-content" id="pageMain">
        ${renderPageSkeleton(title, subtitle)}
      </main>
    </div>
  `;
  return document.getElementById('pageMain');
}