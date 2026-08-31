(() => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  let muted = false;
  function playback(section) {
    if (section.dataset.voiceReady || !window.speechSynthesis) return;
    section.dataset.voiceReady = 'true';
    const text = section.querySelector('.research-answer')?.textContent || section.querySelector('p')?.textContent;
    if (!text) return;
    const controls = document.createElement('div'); controls.className = 'voice-controls';
    const speak = () => {
      if (muted) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text.slice(0,1500) + ' More detail and supporting evidence are shown on screen.');
      window.speechSynthesis.speak(utterance);
    };
    for (const [label, action] of [['Listen to response', speak], ['Replay spoken response', speak], ['Stop speaking', () => window.speechSynthesis.cancel()], ['Mute voice responses', () => {muted=!muted;window.speechSynthesis.cancel();}]]) {
      const button=document.createElement('button');button.type='button';button.textContent=label;
      button.onclick=()=>{action();if(label==='Mute voice responses')button.textContent=muted?'Unmute voice responses':label;};controls.append(button);
    }
    section.append(controls);
  }
  new MutationObserver(() => document.querySelectorAll('.msg.answer > section').forEach(playback))
    .observe(document.documentElement, {childList:true,subtree:true});
  function install() {
    const form = document.querySelector('#chat-form'), input = document.querySelector('#chat-q');
    if (!form || form.dataset.voiceReady) return;
    form.dataset.voiceReady = 'true';
    const mic = document.createElement('button');
    mic.type = 'button'; mic.className = 'voice-start'; mic.dataset.ready = 'true';
    mic.setAttribute('aria-label', 'Dictate a question'); mic.setAttribute('aria-pressed', 'false');
    mic.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/></svg><span>Dictate</span>';
    const status = document.createElement('div'); status.className = 'voice-status active';
    status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
    status.textContent = 'Dictation uses your browser’s speech service. Review the text, then select Send. Do not dictate patient identifiers.';
    form.insertBefore(mic, input); form.insertAdjacentElement('afterend', status);
    if (!Recognition || !window.isSecureContext) {
      mic.disabled = true;
      status.textContent = 'Dictation is unavailable here. Use Chrome on HTTPS with microphone access, or type your question.';
      return;
    }
    mic.addEventListener('click', event => {
      event.preventDefault(); event.stopImmediatePropagation();
      if (recognition) { try { recognition.stop(); } catch (_) { recognition.abort(); } return; }
      let received = false, failed = false;
      recognition = new Recognition(); recognition.lang = navigator.language || 'en-US';
      recognition.interimResults = true; recognition.continuous = false;
      status.textContent = 'Requesting microphone access. Allow the browser permission prompt if shown.';
      mic.disabled = false; mic.setAttribute('aria-label', 'Cancel microphone request'); mic.querySelector('span').textContent = 'Cancel';
      recognition.onstart = () => {
        mic.disabled = false; mic.classList.add('listening'); mic.setAttribute('aria-pressed', 'true');
        mic.setAttribute('aria-label', 'Stop dictation'); mic.querySelector('span').textContent = 'Stop';
        status.textContent = 'Listening… Speak your question. Select Stop when finished.';
      };
      recognition.onresult = event => {
        const transcript = Array.from(event.results).map(result => result[0].transcript).join(' ').trim();
        if (transcript) { received = true; input.value = transcript; input.dispatchEvent(new Event('input', {bubbles:true})); }
      };
      recognition.onerror = event => {
        failed = true;
        const messages = {
          'not-allowed': 'Microphone access was denied. In Chrome, open the site controls beside the address, allow Microphone, then reload. Also check Windows microphone privacy settings.',
          'service-not-allowed': 'The browser speech service is blocked. Check browser or organization settings, or type your question.',
          'audio-capture': 'No microphone was found. Connect one and check your system input device.',
          'network': 'The browser speech service could not connect. Check your connection or type your question.',
          'no-speech': 'No speech was detected. Check your microphone input and try Dictate again.',
          'aborted': 'Dictation stopped. Your text has not been submitted.'
        };
        status.textContent = messages[event.error] || 'Dictation could not complete. Please try again or type your question.';
      };
      recognition.onend = () => {
        recognition = null; mic.disabled = false; mic.classList.remove('listening'); mic.setAttribute('aria-pressed', 'false');
        mic.setAttribute('aria-label', 'Dictate a question'); mic.querySelector('span').textContent = 'Dictate';
        if (!failed) status.textContent = received ? 'Dictation ready. Review your question, then select Send.' : 'No speech captured. Select Dictate to try again, or type your question.';
      };
      try { recognition.start(); } catch (_) {
        recognition = null; mic.disabled = false;
        mic.setAttribute('aria-label', 'Dictate a question'); mic.querySelector('span').textContent = 'Dictate';
        status.textContent = 'The microphone could not start. Check site microphone permission, reload, and try again.';
      }
    }, true);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install); else install();
  window.addEventListener('beforeunload', () => {recognition?.abort();window.speechSynthesis?.cancel();});
})();
