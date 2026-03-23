// =============================================
// COMPONENT: Voice Bar
// =============================================

export function renderVoiceBar() {
  return `
    <div class="voice-bar">
      <button class="mic-btn" id="micBtn">🎙️</button>
      <input
        class="voice-input"
        type="text"
        id="voiceInput"
        placeholder='Speak or type — e.g. "Ahmed and Lina were absent today in class 3G..."'
      />
      <span class="voice-lang-hint">AR · FR · EN</span>
      <button class="btn btn-primary" id="sendBtn" style="padding: 8px 16px; font-size:13px;">Send</button>
    </div>
  `;
}

/**
 * Attach voice bar event listeners after the component is in the DOM.
 * Pass an onSubmit(text) callback to handle agent input.
 *
 * @param {function} onSubmit - called with the trimmed input string
 */
export function initVoiceBar({ onSubmit } = {}) {
  const micBtn    = document.getElementById('micBtn');
  const sendBtn   = document.getElementById('sendBtn');
  const voiceInput = document.getElementById('voiceInput');

  micBtn.addEventListener('click', () => {
    // TODO: hook up Web Speech API or Whisper transcription
    console.log('[VoiceBar] Mic clicked — voice recording coming soon');
    micBtn.textContent = '⏹️';
    setTimeout(() => { micBtn.textContent = '🎙️'; }, 3000);
  });

  const submit = () => {
    const text = voiceInput.value.trim();
    if (!text) return;
    if (typeof onSubmit === 'function') onSubmit(text);
    voiceInput.value = '';
  };

  sendBtn.addEventListener('click', submit);
  voiceInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') submit();
  });
}