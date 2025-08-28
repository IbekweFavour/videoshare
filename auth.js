/* Tiny auth helper to store token + user in localStorage */
const Auth = {
  saveToken(payload){
    localStorage.setItem('VS_TOKEN', payload.access_token);
    localStorage.setItem('VS_USER', JSON.stringify(payload.user));
  },
  token(){ return localStorage.getItem('VS_TOKEN'); },
  currentUser(){ try { return JSON.parse(localStorage.getItem('VS_USER')); } catch(e){ return null; } },
  logout(){ localStorage.removeItem('VS_TOKEN'); localStorage.removeItem('VS_USER'); }
};
