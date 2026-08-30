const status = document.querySelector('#status');
const form = document.querySelector('#onboarding');
const signInButton = document.querySelector('#google-signin');
const fields = document.querySelector('#profile-fields');
let idToken = null, signedInEmail = null;
function message(text, error = false) { status.textContent = text; status.dataset.error = error ? 'true' : 'false'; }
async function bootstrap() {
  const config = await fetch('/api/auth/config').then(r => r.json());
  if (!config.enabled) throw new Error('Google sign-in is not configured yet.');
  const [{initializeApp}, authModule] = await Promise.all([import('https://www.gstatic.com/firebasejs/11.10.0/firebase-app.js'), import('https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js')]);
  const auth = authModule.getAuth(initializeApp(config)), provider = new authModule.GoogleAuthProvider();
  signInButton.addEventListener('click', async () => {
    signInButton.disabled = true; message('Opening secure Google sign-in…');
    try {
      const credential = await authModule.signInWithPopup(auth, provider);
      idToken = await credential.user.getIdToken(); signedInEmail = credential.user.email;
      const response = await fetch('/api/auth/session', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id_token:idToken})});
      if (!response.ok) throw new Error('Fynura could not establish a secure session.');
      const session = await response.json();
      document.querySelector('#signed-in-email').value = signedInEmail;
      fields.hidden = false; signInButton.hidden = true; fields.dataset.owner = session.owner ? 'true' : 'false';
      message('Signed in. Complete your profile to continue.');
    } catch (error) {
      if (error.code === 'auth/popup-blocked') return authModule.signInWithRedirect(auth, provider);
      message(error.message || 'Google sign-in could not be completed.', true); signInButton.disabled = false;
    }
  });
}
form.addEventListener('submit', async event => {
  event.preventDefault(); if (!idToken || !signedInEmail) return message('Sign in with Google first.', true);
  const values = new FormData(form); message('Creating your Fynura profile…');
  try {
    const response = await fetch('/api/onboarding', {method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${idToken}`},body:JSON.stringify({email:signedInEmail,country:values.get('country'),privacy_acknowledged:values.get('privacy_acknowledged')==='on'})});
    const data = await response.json(); if (!response.ok) throw new Error(data.detail?.[0]?.msg || data.detail || 'Could not continue');
    localStorage.fynuraUser=data.user_id; localStorage.fynuraCountry=data.country;
    message('Profile ready. Opening Fynura…');
    document.body.classList.add('is-entering');
    sessionStorage.setItem('fynuraEntryTransition','1');
    const delay=matchMedia('(prefers-reduced-motion: reduce)').matches?0:450;
    setTimeout(()=>{location.href=fields.dataset.owner==='true'?'/admin':'/'},delay);
  } catch(error) { message(error.message,true); }
});
bootstrap().catch(error => message(error.message,true));
