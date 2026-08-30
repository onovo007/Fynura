(() => {
  const button=document.querySelector('#app-signout');if(!button)return;
  const status=document.createElement('p');status.id='signout-status';status.setAttribute('role','status');document.body.append(status);
  button.addEventListener('click',async()=>{
    button.disabled=true;button.textContent='Signing out…';status.textContent='';
    try{
      const response=await fetch('/api/auth/logout',{method:'POST',credentials:'same-origin'});
      if(!response.ok)throw new Error('Sign out failed. Please try again.');
      for(const key of ['fynuraUser','fynuraCountry'])localStorage.removeItem(key);
      sessionStorage.removeItem('fynuraEntryTransition');
      sessionStorage.removeItem('fynuraSession');
      location.replace('/welcome');
    }catch(error){status.textContent=error.message||'Could not sign out. Please try again.';button.disabled=false;button.textContent='Sign out'}
  });
  window.addEventListener('pageshow',event=>{if(event.persisted)location.reload()});
})();
