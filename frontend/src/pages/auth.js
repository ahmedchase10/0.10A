// =============================================
// DIGI-SCHOOL AI — Auth Page (Login / Signup)
// =============================================

import '../styles/auth.css';
import { setSession } from '../auth.js';
import { api } from '../api.js';

// ─── Left panel (shared) ─────────────────────

function renderLeft() {
  return `
    <div class="auth-left">
      <div class="auth-brand">
        <div class="auth-brand-icon">🌿</div>
        <div class="auth-brand-name">
          Digi-School AI
          <span>Teacher Portal</span>
        </div>
      </div>

      <h1 class="auth-headline">
        Your classroom,<br>
        <em>handled.</em>
      </h1>

      <p class="auth-tagline">
        Speak naturally. The agent listens, understands, and takes care of
        everything — attendance, grades, reports, and more. No forms. No clicks.
      </p>

      <div class="auth-features">
        <div class="auth-feature">
          <div class="auth-feature-icon">🎙️</div>
          <div class="auth-feature-text">
            <strong>Voice-first agent</strong> — one sentence marks attendance for the whole class
          </div>
        </div>
        <div class="auth-feature">
          <div class="auth-feature-icon">📝</div>
          <div class="auth-feature-text">
            <strong>AI report cards</strong> — 35 personalized reports generated in under 2 minutes
          </div>
        </div>
        <div class="auth-feature">
          <div class="auth-feature-icon">🚩</div>
          <div class="auth-feature-text">
            <strong>Smart alerts</strong> — agent flags students before problems escalate
          </div>
        </div>
        <div class="auth-feature">
          <div class="auth-feature-icon">🌐</div>
          <div class="auth-feature-text">
            <strong>Arabic · French · English</strong> — works in all three languages
          </div>
        </div>
      </div>
    </div>
  `;
}

// ─── Login form ──────────────────────────────

function renderLoginForm() {
  return `
    <div id="loginForm" class="auth-form">

      <div id="loginBanner" class="auth-banner"></div>

      <div class="auth-field">
        <label class="auth-label">Email</label>
        <div class="auth-input-wrap">
          <span class="auth-input-icon">📧</span>
          <input class="auth-input" id="loginEmail" type="email"
            placeholder="sara.khalil@school.tn" autocomplete="email" />
        </div>
        <span class="auth-error" id="loginEmailErr">Please enter a valid email address.</span>
      </div>

      <div class="auth-field">
        <label class="auth-label">Password</label>
        <div class="auth-input-wrap">
          <span class="auth-input-icon">🔒</span>
          <input class="auth-input" id="loginPassword" type="password"
            placeholder="Your password" autocomplete="current-password" />
          <button class="auth-eye" id="loginEye" tabindex="-1">👁</button>
        </div>
        <span class="auth-error" id="loginPasswordErr">Password is required.</span>
      </div>

      <div class="auth-forgot">Forgot password?</div>

      <button class="auth-submit" id="loginBtn">
        Sign In
        <span class="spinner"></span>
      </button>

    </div>
  `;
}

// ─── Signup form ─────────────────────────────

function renderSignupForm() {
  return `
    <div id="signupForm" class="auth-form" style="display:none">

      <div id="signupBanner" class="auth-banner"></div>

      <div class="auth-field">
        <label class="auth-label">Full Name</label>
        <div class="auth-input-wrap">
          <span class="auth-input-icon">👤</span>
          <input class="auth-input" id="signupName" type="text"
            placeholder="e.g. Sara Khalil" autocomplete="name" />
        </div>
        <span class="auth-error" id="signupNameErr">Full name is required.</span>
      </div>

      <div class="auth-field">
        <label class="auth-label">Email</label>
        <div class="auth-input-wrap">
          <span class="auth-input-icon">📧</span>
          <input class="auth-input" id="signupEmail" type="email"
            placeholder="sara.khalil@school.tn" autocomplete="email" />
        </div>
        <span class="auth-error" id="signupEmailErr">Please enter a valid email address.</span>
      </div>

      <div class="auth-field">
        <label class="auth-label">Subject</label>
        <div class="auth-input-wrap">
          <span class="auth-input-icon">📚</span>
          <input class="auth-input" id="signupSubject" type="text"
            placeholder="e.g. English, Maths, Physics" />
        </div>
      </div>

      <div class="auth-field">
        <label class="auth-label">Password</label>
        <div class="auth-input-wrap">
          <span class="auth-input-icon">🔒</span>
          <input class="auth-input" id="signupPassword" type="password"
            placeholder="At least 8 characters" autocomplete="new-password" />
          <button class="auth-eye" id="signupEye" tabindex="-1">👁</button>
        </div>
        <span class="auth-error" id="signupPasswordErr">Password must be at least 8 characters.</span>
      </div>

      <div class="auth-field">
        <label class="auth-label">Confirm Password</label>
        <div class="auth-input-wrap">
          <span class="auth-input-icon">🔒</span>
          <input class="auth-input" id="signupConfirm" type="password"
            placeholder="Repeat your password" autocomplete="new-password" />
        </div>
        <span class="auth-error" id="signupConfirmErr">Passwords do not match.</span>
      </div>

      <button class="auth-submit" id="signupBtn">
        Create Account
        <span class="spinner"></span>
      </button>

    </div>
  `;
}

// ─── Right panel ─────────────────────────────

function renderRight(activeTab = 'login') {
  return `
    <div class="auth-right">
      <div class="auth-form-wrap">

        <div class="auth-form-title">
          Welcome to <span>Digi-School</span>
        </div>
        <p class="auth-form-sub">Sign in to your teacher account or create a new one.</p>

        <div class="auth-tabs">
          <button class="auth-tab ${activeTab === 'login'  ? 'active' : ''}" id="tabLogin">Sign In</button>
          <button class="auth-tab ${activeTab === 'signup' ? 'active' : ''}" id="tabSignup">Create Account</button>
        </div>

        ${renderLoginForm()}
        ${renderSignupForm()}

        <div class="auth-switch" id="authSwitch">
          Don't have an account? <a id="switchToSignup">Create one</a>
        </div>

      </div>
    </div>
  `;
}

// ─── Helpers ─────────────────────────────────

function showBanner(id, type, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `auth-banner ${type}`;
  el.innerHTML = `<span>${type === 'error' ? '⚠️' : '✓'}</span> ${msg}`;
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.classList.toggle('loading', loading);
  btn.childNodes[0].textContent = loading
    ? (btnId === 'loginBtn' ? 'Signing in...' : 'Creating account...')
    : (btnId === 'loginBtn' ? 'Sign In' : 'Create Account');
}

function showError(id, show) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('visible', show);
}

function markInput(id, hasError) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('error', hasError);
}

// ─── Login logic ─────────────────────────────

function initLogin(onSuccess) {
  const btn = document.getElementById('loginBtn');
  const eye = document.getElementById('loginEye');

  // toggle password visibility
  eye?.addEventListener('click', () => {
    const input = document.getElementById('loginPassword');
    input.type = input.type === 'password' ? 'text' : 'password';
  });

  // enter key submits
  ['loginEmail','loginPassword'].forEach(id => {
    document.getElementById(id)?.addEventListener('keydown', e => {
      if (e.key === 'Enter') btn.click();
    });
  });

  btn?.addEventListener('click', async () => {
    const email    = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;

    // ── Client validation ──
    let valid = true;
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    markInput('loginEmail', !emailOk);
    showError('loginEmailErr', !emailOk);
    if (!emailOk) valid = false;

    if (!password) {
      markInput('loginPassword', true);
      showError('loginPasswordErr', true);
      valid = false;
    } else {
      markInput('loginPassword', false);
      showError('loginPasswordErr', false);
    }

    if (!valid) return;

    setLoading('loginBtn', true);

    try {
      const data = await api.auth.login(email, password);
      setSession(data.teacher, data.token);
      showBanner('loginBanner', 'success', 'Login successful! Redirecting...');
      setTimeout(() => onSuccess(), 600);

    } catch (err) {
      showBanner('loginBanner', 'error', err.message || 'Invalid email or password.');
    } finally {
      setLoading('loginBtn', false);
    }
  });
}

// ─── Signup logic ────────────────────────────

function initSignup(onSuccess) {
  const btn = document.getElementById('signupBtn');
  const eye = document.getElementById('signupEye');

  eye?.addEventListener('click', () => {
    const input = document.getElementById('signupPassword');
    input.type = input.type === 'password' ? 'text' : 'password';
  });

  btn?.addEventListener('click', async () => {
    const name     = document.getElementById('signupName').value.trim();
    const email    = document.getElementById('signupEmail').value.trim();
    const subject  = document.getElementById('signupSubject').value.trim();
    const password = document.getElementById('signupPassword').value;
    const confirm  = document.getElementById('signupConfirm').value;

    // ── Client validation ──
    let valid = true;

    markInput('signupName', !name);
    showError('signupNameErr', !name);
    if (!name) valid = false;

    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    markInput('signupEmail', !emailOk);
    showError('signupEmailErr', !emailOk);
    if (!emailOk) valid = false;

    const passOk = password.length >= 8;
    markInput('signupPassword', !passOk);
    showError('signupPasswordErr', !passOk);
    if (!passOk) valid = false;

    const confirmOk = password === confirm;
    markInput('signupConfirm', !confirmOk);
    showError('signupConfirmErr', !confirmOk);
    if (!confirmOk) valid = false;

    if (!valid) return;

    setLoading('signupBtn', true);

    try {
      const data = await api.auth.register(name, email, password, subject);
      setSession(data.teacher, data.token);
      showBanner('signupBanner', 'success', 'Account created! Redirecting...');
      setTimeout(() => onSuccess(), 600);

    } catch (err) {
      showBanner('signupBanner', 'error', err.message || 'Could not create account. Try again.');
    } finally {
      setLoading('signupBtn', false);
    }
  });
}

// ─── Tab switching ────────────────────────────

function initTabs() {
  const tabLogin   = document.getElementById('tabLogin');
  const tabSignup  = document.getElementById('tabSignup');
  const loginForm  = document.getElementById('loginForm');
  const signupForm = document.getElementById('signupForm');
  const authSwitch = document.getElementById('authSwitch');
  const switchLink = document.getElementById('switchToSignup');

  function goLogin() {
    tabLogin.classList.add('active');
    tabSignup.classList.remove('active');
    loginForm.style.display  = 'flex';
    signupForm.style.display = 'none';
    authSwitch.innerHTML = `Don't have an account? <a id="switchToSignup">Create one</a>`;
    document.getElementById('switchToSignup').addEventListener('click', goSignup);
  }

  function goSignup() {
    tabSignup.classList.add('active');
    tabLogin.classList.remove('active');
    signupForm.style.display = 'flex';
    loginForm.style.display  = 'none';
    authSwitch.innerHTML = `Already have an account? <a id="switchToLogin">Sign in</a>`;
    document.getElementById('switchToLogin').addEventListener('click', goLogin);
  }

  tabLogin.addEventListener('click', goLogin);
  tabSignup.addEventListener('click', goSignup);
  switchLink?.addEventListener('click', goSignup);
}

// ─── Main Render ─────────────────────────────

export function renderAuth(appEl, onLoginSuccess) {
  appEl.innerHTML = `
    <div class="bg-layer"></div>
    <div class="bg-globe"></div>
    <div class="auth-page">
      ${renderLeft()}
      ${renderRight()}
    </div>
  `;

  initTabs();
  initLogin(onLoginSuccess);
  initSignup(onLoginSuccess);
}