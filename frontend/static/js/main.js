// ═══════════════════════════════════════════════════════════════════
//  NutriTrack · main.js
// ═══════════════════════════════════════════════════════════════════
const API = 'http://127.0.0.1:5000/api';
let accessToken = localStorage.getItem('nt_access')  || null;
let currentUser = null;
let adminPage   = 1;
let currentTab  = 'daily';

// ── AUTH HEADERS ─────────────────────────────────────────────────
function authHeaders() {
  return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${accessToken}` };
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, { ...opts, headers: { ...(opts.headers || {}), ...authHeaders() } });
  if (res.status === 401) { logout(); return null; }
  return res;
}

function saveTokens(access, refresh) {
  accessToken = access;
  localStorage.setItem('nt_access',  access);
  localStorage.setItem('nt_refresh', refresh);
}

function clearTokens() {
  accessToken = null;
  localStorage.removeItem('nt_access');
  localStorage.removeItem('nt_refresh');
}

// ── TOAST ────────────────────────────────────────────────────────
function toast(msg, type = 'success') {
  const c  = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span>${{success:'✓',error:'✕',info:'ℹ',warning:'⚠'}[type]||'•'}</span><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function showAuthError(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 6000);
}

// ── SCREEN NAV ───────────────────────────────────────────────────
function showScreen(id) {
  document.querySelectorAll('.auth-screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
}

function showPage(navEl) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  navEl.classList.add('active');
  document.getElementById('page-' + navEl.dataset.page).classList.add('active');
  if (navEl.dataset.page === 'analytics') loadAnalyticsTab(currentTab);
  if (navEl.dataset.page === 'admin') { loadAdminStats(); loadAdminUsers(); }
}

function togglePw(id, btn) {
  const inp = document.getElementById(id);
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁' : '🙈';
}

// ── INIT ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  setDateDefaults();
  checkResetToken();

  if (accessToken) {
    const ok = await loadCurrentUser();
    if (ok) enterApp();
  }
});

function setDateDefaults() {
  const today = new Date().toISOString().split('T')[0];
  ['log-date', 'analytics-date'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = today;
  });
  const dd = document.getElementById('dash-date');
  if (dd) dd.textContent = new Date().toLocaleDateString('en-IN', { weekday:'long', year:'numeric', month:'long', day:'numeric' });
}

function checkResetToken() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('token')) {
    showScreen('screenReset');
    window._resetToken = params.get('token');
  }
  if (params.get('verified') === '1') {
    showScreen('screenLogin');
    toast('Email verified! You can now log in.', 'success');
  }
}

// ── LOAD USER ────────────────────────────────────────────────────
async function loadCurrentUser() {
  try {
    const res = await apiFetch('/auth/me');
    if (!res || !res.ok) { clearTokens(); return false; }
    const data = await res.json();
    currentUser = data.user;
    populateSidebar(currentUser);
    if (data.stats && data.stats.bmr) {
      setStat('stat-bmr',  data.stats.bmr);
      setStat('stat-tdee', data.stats.tdee);
      populateProfilePage(currentUser, data.stats);
    }
    return true;
  } catch { clearTokens(); return false; }
}

function populateSidebar(user) {
  setText('sb-name',  user.name  || 'User');
  setText('sb-email', user.email || '');

  const badge = document.getElementById('sb-role-badge');
  if (badge) {
    badge.textContent  = user.role;
    badge.className    = `role-badge ${user.role}`;
    badge.style.display = 'inline-block';
  }

  // Admin nav
  const adminNav = document.getElementById('adminNavItem');
  if (adminNav) adminNav.style.display = user.role === 'admin' ? 'flex' : 'none';

  // Verify banner
  const banner = document.getElementById('verifyBanner');
  if (banner) banner.style.display = user.is_verified ? 'none' : 'block';
}

function enterApp() {
  document.querySelectorAll('.auth-screen').forEach(s => s.classList.remove('active'));
  document.getElementById('setupOverlay').classList.remove('active');
  document.getElementById('appShell').classList.add('active');

  if (!currentUser.profile_complete) {
    document.getElementById('setupOverlay').classList.add('active');
  } else {
    loadDashboard();
    loadTodayLogs();
  }
}

// ── SIGNUP ───────────────────────────────────────────────────────
async function signup() {
  const name    = v('signup-name').trim();
  const email   = v('signup-email').trim();
  const pw      = v('signup-password');
  const confirm = v('signup-confirm');

  if (!name || !email || !pw)  { showAuthError('signupError', 'Please fill in all fields'); return; }
  if (pw !== confirm)           { showAuthError('signupError', 'Passwords do not match'); return; }
  if (pw.length < 6)            { showAuthError('signupError', 'Password must be at least 6 characters'); return; }

  const btn = setBtnLoading('signupBtn', 'Creating…');
  try {
    const res  = await fetch(`${API}/auth/register`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name,email,password:pw}) });
    const data = await res.json();
    if (!res.ok) { showAuthError('signupError', data.error || 'Signup failed'); return; }
    saveTokens(data.access_token, data.refresh_token);
    currentUser = data.user;
    populateSidebar(currentUser);
    enterApp();
    toast(`Welcome, ${data.user.name}! 🎉`);
    if (!data.is_verified) toast('Check your email to verify your account 📧', 'info');
  } catch { showAuthError('signupError', 'Connection error. Is the server running?'); }
  finally { resetBtn(btn, 'Create Account →'); }
}

// ── LOGIN ────────────────────────────────────────────────────────
async function login() {
  const email = v('login-email').trim();
  const pw    = v('login-password');
  if (!email || !pw) { showAuthError('loginError', 'Please enter your email and password'); return; }

  const btn = setBtnLoading('loginBtn', 'Signing in…');
  try {
    const res  = await fetch(`${API}/auth/login`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email,password:pw}) });
    const data = await res.json();
    if (!res.ok) { showAuthError('loginError', data.error || 'Login failed'); return; }
    saveTokens(data.access_token, data.refresh_token);
    currentUser = data.user;
    populateSidebar(currentUser);
    enterApp();
    toast(`Welcome back, ${data.user.name}!`);
  } catch { showAuthError('loginError', 'Connection error. Is the server running?'); }
  finally { resetBtn(btn, 'Sign In →'); }
}

// Enter key support
document.addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  if (document.getElementById('screenLogin').classList.contains('active'))  login();
  if (document.getElementById('screenSignup').classList.contains('active')) signup();
  if (document.getElementById('screenForgot').classList.contains('active')) forgotPassword();
  if (document.getElementById('screenReset').classList.contains('active'))  resetPassword();
});

// ── FORGOT PASSWORD ──────────────────────────────────────────────
async function forgotPassword() {
  const email = v('forgot-email').trim();
  if (!email) { showAuthError('forgotError', 'Please enter your email'); return; }

  const btn = setBtnLoading('forgotBtn', 'Sending…');
  try {
    const res  = await fetch(`${API}/auth/forgot-password`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email}) });
    const data = await res.json();
    document.getElementById('forgotSuccess').style.display = 'block';
    document.getElementById('forgotSuccess').textContent   = data.message;
  } catch { showAuthError('forgotError', 'Connection error'); }
  finally { resetBtn(btn, 'Send Reset Link'); }
}

// ── RESET PASSWORD ───────────────────────────────────────────────
async function resetPassword() {
  const token   = window._resetToken || new URLSearchParams(window.location.search).get('token');
  const pw      = v('reset-password');
  const confirm = v('reset-confirm');
  if (!pw || !confirm)   { showAuthError('resetError', 'Please fill in both fields'); return; }
  if (pw !== confirm)    { showAuthError('resetError', 'Passwords do not match'); return; }
  if (pw.length < 6)     { showAuthError('resetError', 'Password must be at least 6 characters'); return; }
  if (!token)            { showAuthError('resetError', 'Invalid reset link'); return; }

  const btn = setBtnLoading('resetBtn', 'Resetting…');
  try {
    const res  = await fetch(`${API}/auth/reset-password`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({token, new_password:pw}) });
    const data = await res.json();
    if (!res.ok) { showAuthError('resetError', data.error || 'Reset failed'); return; }
    toast('Password reset! Please log in.');
    window.history.replaceState({}, '', '/');
    showScreen('screenLogin');
  } catch { showAuthError('resetError', 'Connection error'); }
  finally { resetBtn(btn, 'Reset Password →'); }
}

// ── RESEND VERIFICATION ──────────────────────────────────────────
async function resendVerification() {
  const res = await apiFetch('/auth/resend-verification', { method:'POST' });
  if (!res) return;
  const data = await res.json();
  toast(data.message || 'Verification email sent', res.ok ? 'success' : 'error');
}

// ── LOGOUT ───────────────────────────────────────────────────────
function logout() {
  clearTokens();
  currentUser = null;
  document.getElementById('appShell').classList.remove('active');
  showScreen('screenLogin');
  toast('Signed out', 'info');
}

// ── PROFILE SETUP ────────────────────────────────────────────────
async function saveProfile() {
  const payload = {
    age:              parseInt(v('setup-age')),
    gender:           v('setup-gender'),
    height_cm:        parseFloat(v('setup-height')),
    weight_kg:        parseFloat(v('setup-weight')),
    activity_level:   v('setup-activity'),
    goal:             v('setup-goal'),
    target_weight_kg: parseFloat(v('setup-target-weight')) || null,
    target_days:      parseInt(v('setup-target-days'))      || null,
  };
  if (!payload.age || !payload.height_cm || !payload.weight_kg) { toast('Please fill in all required fields', 'error'); return; }

  const btn = setBtnLoading('setupBtn', 'Saving…');
  try {
    const res  = await apiFetch('/user/profile', { method:'PUT', body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) { toast(data.error || 'Failed', 'error'); return; }
    currentUser = data.user;
    populateSidebar(currentUser);
    populateProfilePage(currentUser, data.stats);
    document.getElementById('setupOverlay').classList.remove('active');
    toast('Profile saved! Let\'s track 🎯');
    loadDashboard();
    loadTodayLogs();
  } catch { toast('Error saving profile', 'error'); }
  finally { resetBtn(btn, 'Save & Start Tracking →'); }
}

// ── DASHBOARD ────────────────────────────────────────────────────
async function loadDashboard() {
  if (!currentUser?.profile_complete) return;
  try {
    const today = new Date().toISOString().split('T')[0];
    const res   = await apiFetch(`/analytics/daily?date=${today}`);
    if (!res) return;
    const d = await res.json();
    const a = d.actual, g = d.goals, p = d.prediction;

    updateRing(a.calories, g.calories);
    updateBar('protein', a.protein_g,  g.protein_g);
    updateBar('carbs',   a.carbs_g,    g.carbs_g);
    updateBar('fat',     a.fat_g,      g.fat_g);
    updateBar('fiber',   a.fiber_g,    g.fiber_g);

    const rem   = Math.round(g.calories - a.calories);
    const remEl = document.getElementById('stat-remaining');
    if (remEl) { remEl.textContent = Math.abs(rem); remEl.style.color = rem < 0 ? 'var(--rose)' : 'var(--violet)'; }
    setStat('stat-sodium', Math.round(a.sodium_mg));

    if (p) {
      const pw  = p.predicted_weight;
      const d7  = (pw.after_7_days_kg  - currentUser.weight_kg).toFixed(1);
      const d30 = (pw.after_30_days_kg - currentUser.weight_kg).toFixed(1);
      setText('pred-now',       currentUser.weight_kg + ' kg');
      setText('pred-7d',        pw.after_7_days_kg  + ' kg');
      setText('pred-30d',       pw.after_30_days_kg + ' kg');
      setDelta('pred-7d-delta',  d7);
      setDelta('pred-30d-delta', d30);
    }
    if (d.charts && a.calories > 0) {
      showChart('chartGoalActual', 'chartGoalActualEmpty', d.charts.goal_vs_actual);
      showChart('chartMacro',      'chartMacroEmpty',      d.charts.macro_breakdown);
    }
  } catch(e) { console.error('Dashboard error', e); }
}

function updateRing(actual, goal) {
  const pct    = Math.min(actual / goal, 1);
  const offset = 283 - 283 * pct;
  const ring   = document.getElementById('ringFill');
  if (!ring) return;
  ring.style.strokeDashoffset = offset;
  setText('ringKcal', Math.round(actual));
  setText('ringOf',   `/ ${Math.round(goal)} kcal`);
  const over = actual > goal;
  ring.classList.toggle('over', over);
  document.getElementById('ringKcal')?.classList.toggle('over', over);
}

function updateBar(name, actual, goal) {
  const pct = goal > 0 ? Math.min((actual / goal) * 100, 100) : 0;
  const bar  = document.getElementById('bar-' + name);
  const lbl  = document.getElementById('bar-' + name + '-val');
  if (bar) bar.style.width = pct + '%';
  if (lbl) lbl.textContent = `${Math.round(actual)}/${Math.round(goal)}g`;
}

// ── LOG FOOD ─────────────────────────────────────────────────────
async function logFood() {
  const input = v('foodInput').trim();
  if (!input) { toast('Please enter what you ate', 'error'); return; }

  const btn = setBtnLoading('logBtn', '…');
  try {
    const res  = await apiFetch('/food/log', { method:'POST', body: JSON.stringify({ food_input:input, meal_type:v('meal-type'), log_date:v('log-date') }) });
    if (!res) return;
    const data = await res.json();
    if (!res.ok) { toast(data.error || 'Failed to log', 'error'); return; }
    toast(`Logged ${data.total_nutrients.calories} kcal ✓`);
    document.getElementById('foodInput').value = '';
    showParsePreview(data.parsed_items, data.total_nutrients);
    loadTodayLogs();
    loadDashboard();
  } catch { toast('Error logging food', 'error'); }
  finally { resetBtn(btn, '<span>Log</span><span>→</span>'); }
}

function showParsePreview(items, totals) {
  const wrap = document.getElementById('parsePreview');
  if (!wrap) return;
  wrap.innerHTML = `
    <div class="card-title">✅ Parsed Items</div>
    ${items.map(item => `
      <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--faint)">
        <div style="flex:1">
          <div style="font-weight:600;text-transform:capitalize">${item.name}</div>
          <div style="font-size:12px;color:var(--muted)">${item.quantity} ${item.unit} = ${item.grams}g</div>
        </div>
        <span class="pill">${item.nutrients.calories} kcal</span>
        <span class="pill pill-amber">P: ${item.nutrients.protein}g</span>
      </div>`).join('')}
    <div style="padding:12px 0;display:flex;gap:16px;font-family:var(--mono);font-size:13px">
      <span style="color:var(--teal)">Total: ${totals.calories} kcal</span>
      <span style="color:var(--violet)">P: ${totals.protein_g}g</span>
      <span style="color:var(--amber)">C: ${totals.carbs_g}g</span>
      <span style="color:var(--rose)">F: ${totals.fat_g}g</span>
    </div>`;
  wrap.style.display = 'block';
}

async function loadTodayLogs() {
  const today = new Date().toISOString().split('T')[0];
  const wrap  = document.getElementById('logTableWrap');
  if (!wrap) return;
  wrap.innerHTML = '<div class="loading-state"><div class="spinner"></div> Loading…</div>';
  try {
    const res  = await apiFetch(`/food/log?date=${today}`);
    if (!res) return;
    const data = await res.json();
    if (!data.logs?.length) {
      wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">🍽️</div><div class="empty-title">No meals logged today</div></div>`;
      return;
    }
    wrap.innerHTML = `
      <table class="log-table">
        <thead><tr><th>Food</th><th>Meal</th><th>Kcal</th><th>Protein</th><th>Carbs</th><th>Fat</th><th></th></tr></thead>
        <tbody>
          ${data.logs.map(log => `
            <tr>
              <td>
                <div style="font-weight:500">${log.raw_input}</div>
                <div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:3px">
                  ${log.food_items.map(i=>`<span class="pill">${i.name} ${i.grams}g</span>`).join('')}
                </div>
              </td>
              <td><span class="meal-badge meal-${log.meal_type}">${log.meal_type}</span></td>
              <td class="num" style="color:var(--teal)">${log.nutrients.calories}</td>
              <td class="num" style="color:var(--violet)">${log.nutrients.protein_g}g</td>
              <td class="num" style="color:var(--amber)">${log.nutrients.carbs_g}g</td>
              <td class="num" style="color:var(--rose)">${log.nutrients.fat_g}g</td>
              <td><button class="btn btn-danger btn-sm" onclick="deleteLog(${log.id})">✕</button></td>
            </tr>`).join('')}
        </tbody>
      </table>`;
  } catch(e) { wrap.innerHTML = errState(e.message); }
}

async function deleteLog(id) {
  if (!confirm('Remove this entry?')) return;
  await apiFetch(`/food/log/${id}`, { method:'DELETE' });
  toast('Entry removed');
  loadTodayLogs();
  loadDashboard();
}

// ── ANALYTICS ────────────────────────────────────────────────────
function switchTab(tab) {
  currentTab = tab;
  ['daily','weekly','monthly'].forEach(t => {
    document.getElementById('atab-'+t).style.display = t===tab ? 'block' : 'none';
    const btn = document.getElementById('tab-'+t);
    if (btn) btn.className = t===tab ? 'btn btn-primary' : 'btn btn-ghost';
  });
  loadAnalyticsTab(tab);
}

function loadAnalyticsTab(tab) {
  if (tab==='daily')   loadDailyAnalytics();
  else if (tab==='weekly')  loadWeeklyAnalytics();
  else loadMonthlyAnalytics();
}

async function loadDailyAnalytics() {
  const date    = v('analytics-date');
  const content = document.getElementById('daily-content');
  content.innerHTML = '<div class="loading-state"><div class="spinner"></div> Loading…</div>';
  try {
    const res = await apiFetch(`/analytics/daily?date=${date}`);
    if (!res) return;
    const d   = await res.json();
    content.innerHTML = `
      <div class="nutrient-grid" style="margin-bottom:16px">
        ${ncCard('Calories','kcal',d.actual.calories,d.goals.calories,'var(--teal)')}
        ${ncCard('Protein','g',d.actual.protein_g,d.goals.protein_g,'var(--violet)')}
        ${ncCard('Carbs','g',d.actual.carbs_g,d.goals.carbs_g,'var(--amber)')}
        ${ncCard('Fat','g',d.actual.fat_g,d.goals.fat_g,'var(--rose)')}
        ${ncCard('Fiber','g',d.actual.fiber_g,d.goals.fiber_g,'var(--teal)')}
        ${ncCard('Sugar','g',d.actual.sugar_g,d.goals.sugar_g,'var(--amber)')}
        ${ncCard('Sodium','mg',d.actual.sodium_mg,d.goals.sodium_mg,'var(--rose)')}
        ${ncCard('Vit C','mg',d.actual.vitamin_c_mg,90,'var(--teal)')}
      </div>
      ${d.prediction ? predHTML(d.prediction) : ''}
      <div class="grid-2" style="margin-top:16px">
        <div class="card"><div class="card-title">Goal vs Actual</div><img src="${d.charts.goal_vs_actual}" class="chart-img"/></div>
        <div class="card"><div class="card-title">Macros</div><img src="${d.charts.macro_breakdown}" class="chart-img"/></div>
      </div>`;
  } catch(e) { content.innerHTML = errState(e.message); }
}

async function loadWeeklyAnalytics() {
  const content = document.getElementById('weekly-content');
  content.innerHTML = '<div class="loading-state"><div class="spinner"></div> Loading…</div>';
  try {
    const res = await apiFetch('/analytics/weekly');
    if (!res) return;
    const d   = await res.json();
    const avg = d.week_average, wg = d.weekly_goals;
    content.innerHTML = `
      <div class="grid-4" style="margin-bottom:16px">
        ${ncCard('Avg Cal','kcal/d',avg.calories,Math.round(wg.calories/7),'var(--teal)')}
        ${ncCard('Avg Protein','g/d',avg.protein_g,Math.round(wg.protein_g/7),'var(--violet)')}
        ${ncCard('Avg Carbs','g/d',avg.carbs_g,Math.round(wg.carbs_g/7),'var(--amber)')}
        ${ncCard('Avg Fat','g/d',avg.fat_g,Math.round(wg.fat_g/7),'var(--rose)')}
      </div>
      <div class="card" style="margin-bottom:16px">
        <div class="card-title">Day-by-Day</div>
        <table class="log-table">
          <thead><tr><th>Date</th><th>Calories</th><th>Protein</th><th>Carbs</th><th>Fat</th><th>Fiber</th></tr></thead>
          <tbody>${d.daily_summaries.map(day=>`
            <tr>
              <td style="color:var(--muted);font-size:12px">${day.date}</td>
              <td class="num" style="color:var(--teal)">${day.calories}</td>
              <td class="num" style="color:var(--violet)">${day.protein_g}g</td>
              <td class="num" style="color:var(--amber)">${day.carbs_g}g</td>
              <td class="num" style="color:var(--rose)">${day.fat_g}g</td>
              <td class="num">${day.fiber_g}g</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      <div class="grid-2">
        <div class="card"><div class="card-title">Calorie Trend</div><img src="${d.charts.calorie_trend}" class="chart-img"/></div>
        <div class="card"><div class="card-title">Weekly Goal vs Actual</div><img src="${d.charts.goal_vs_actual}" class="chart-img"/></div>
      </div>`;
  } catch(e) { content.innerHTML = errState(e.message); }
}

async function loadMonthlyAnalytics() {
  const content = document.getElementById('monthly-content');
  content.innerHTML = '<div class="loading-state"><div class="spinner"></div> Loading…</div>';
  try {
    const res = await apiFetch('/analytics/monthly');
    if (!res) return;
    const d   = await res.json();
    const avg = d.month_average_per_day, mg = d.monthly_goals;
    content.innerHTML = `
      <div class="grid-4" style="margin-bottom:16px">
        ${ncCard('Avg Cal','kcal/d',avg.calories,Math.round(mg.calories/30),'var(--teal)')}
        ${ncCard('Avg Protein','g/d',avg.protein_g,Math.round(mg.protein_g/30),'var(--violet)')}
        ${ncCard('Avg Carbs','g/d',avg.carbs_g,Math.round(mg.carbs_g/30),'var(--amber)')}
        ${ncCard('Avg Fat','g/d',avg.fat_g,Math.round(mg.fat_g/30),'var(--rose)')}
      </div>
      <div class="card" style="margin-bottom:16px">
        <div style="font-size:13px;color:var(--muted)">
          Period: <strong style="color:var(--text)">${d.period.start} → ${d.period.end}</strong>
          &nbsp;·&nbsp; Days logged: <strong style="color:var(--teal)">${d.logged_days}</strong>
        </div>
      </div>
      <div class="card"><div class="card-title">Monthly Goal vs Actual</div><img src="${d.charts.goal_vs_actual}" class="chart-img"/></div>`;
  } catch(e) { content.innerHTML = errState(e.message); }
}

// ── PROFILE ──────────────────────────────────────────────────────
function populateProfilePage(user, stats) {
  const map = { 'p-name':user.name,'p-age':user.age,'p-gender':user.gender,'p-height':user.height_cm,
    'p-weight':user.weight_kg,'p-activity':user.activity_level,'p-goal':user.goal,
    'p-target-weight':user.target_weight_kg||'','p-target-days':user.target_days||'','p-email':user.email };
  for (const [id, val] of Object.entries(map)) {
    const el = document.getElementById(id);
    if (el) el.value = val ?? '';
  }
  if (stats) {
    setStat('p-bmr',        stats.bmr);
    setStat('p-tdee',       stats.tdee);
    setStat('p-cal-target', stats.calorie_target);
    setStat('stat-bmr',     stats.bmr);
    setStat('stat-tdee',    stats.tdee);
  }
  const vb = document.getElementById('p-verified-badge');
  if (vb) vb.innerHTML = user.is_verified
    ? '<span class="badge badge-green">✓ Verified</span>'
    : '<span class="badge badge-amber">⚠ Unverified</span>';
}

async function updateProfile() {
  const payload = {
    name:user_name(), age:+v('p-age'), gender:v('p-gender'),
    height_cm:+v('p-height'), weight_kg:+v('p-weight'),
    activity_level:v('p-activity'), goal:v('p-goal'),
    target_weight_kg:+v('p-target-weight')||null, target_days:+v('p-target-days')||null,
  };
  try {
    const res  = await apiFetch('/user/profile/update', { method:'PUT', body:JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) { toast(data.error||'Update failed','error'); return; }
    currentUser = data.user;
    populateSidebar(currentUser);
    populateProfilePage(currentUser, data.stats);
    toast('Profile updated ✓');
    loadDashboard();
  } catch { toast('Error updating profile','error'); }
}
function user_name(){return v('p-name')}

async function changePassword() {
  const curr = v('p-curr-pw'), newpw = v('p-new-pw');
  if (!curr||!newpw) { toast('Please fill in both fields','error'); return; }
  const res  = await apiFetch('/auth/change-password', { method:'POST', body:JSON.stringify({current_password:curr,new_password:newpw}) });
  const data = await res.json();
  if (!res.ok) { toast(data.error||'Failed','error'); return; }
  toast('Password changed ✓');
  document.getElementById('p-curr-pw').value = '';
  document.getElementById('p-new-pw').value  = '';
}

async function confirmDeleteAccount() {
  if (!confirm('Delete your account and ALL food logs permanently? This cannot be undone.')) return;
  if (!confirm('Are you absolutely sure?')) return;
  await apiFetch('/auth/delete-account', { method:'DELETE' });
  logout();
  toast('Account deleted','info');
}

// ── ADMIN ────────────────────────────────────────────────────────
async function loadAdminStats() {
  try {
    const res  = await apiFetch('/admin/stats');
    if (!res || !res.ok) return;
    const d    = await res.json();
    setStat('a-total-users', d.users.total);
    setStat('a-verified',    d.users.verified);
    setStat('a-new-7d',      d.users.new_7d);
    setStat('a-total-logs',  d.food_logs.total);
  } catch {}
}

async function loadAdminUsers(page = adminPage) {
  adminPage = page;
  const search = v('admin-search');
  const role   = v('admin-role-filter');
  const wrap   = document.getElementById('adminUsersTable');
  if (!wrap) return;
  wrap.innerHTML = '<div class="loading-state"><div class="spinner"></div> Loading…</div>';
  try {
    const params = new URLSearchParams({ page, per_page:15, search, role });
    const res    = await apiFetch(`/admin/users?${params}`);
    if (!res || !res.ok) { wrap.innerHTML = errState('Access denied'); return; }
    const d = await res.json();

    if (!d.users.length) { wrap.innerHTML = '<div class="empty-state"><div class="empty-icon">👤</div><div>No users found</div></div>'; return; }

    wrap.innerHTML = `
      <table class="admin-table">
        <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Role</th><th>Verified</th><th>Active</th><th>Joined</th><th>Actions</th></tr></thead>
        <tbody>
          ${d.users.map(u => `
            <tr>
              <td class="num" style="color:var(--muted)">${u.id}</td>
              <td style="font-weight:500">${u.name||'—'}</td>
              <td style="color:var(--muted);font-size:12px">${u.email}</td>
              <td><span class="badge ${u.role==='admin'?'badge-violet':'badge-green'}">${u.role}</span></td>
              <td>${u.is_verified?'<span class="badge badge-green">✓</span>':'<span class="badge badge-amber">✗</span>'}</td>
              <td>${u.is_active?'<span class="badge badge-green">Yes</span>':'<span class="badge badge-rose">No</span>'}</td>
              <td style="color:var(--muted);font-size:12px">${u.created_at?.split('T')[0]||'—'}</td>
              <td>
                <div class="action-btn-group">
                  ${u.role!=='admin'
                    ? `<button class="btn btn-warning btn-sm" onclick="promoteUser(${u.id})">Make Admin</button>`
                    : `<button class="btn btn-ghost btn-sm" onclick="demoteUser(${u.id})">Demote</button>`}
                  ${u.is_active
                    ? `<button class="btn btn-danger btn-sm" onclick="toggleUserActive(${u.id},false)">Disable</button>`
                    : `<button class="btn btn-ghost btn-sm" onclick="toggleUserActive(${u.id},true)">Enable</button>`}
                  ${!u.is_verified
                    ? `<button class="btn btn-ghost btn-sm" onclick="verifyUser(${u.id})">Verify</button>` : ''}
                </div>
              </td>
            </tr>`).join('')}
        </tbody>
      </table>`;

    // Pagination
    const pg = document.getElementById('adminPagination');
    pg.innerHTML = '';
    for (let i = 1; i <= d.pages; i++) {
      const b = document.createElement('button');
      b.textContent = i;
      b.className = `btn btn-sm ${i===page?'btn-primary':'btn-ghost'}`;
      b.onclick = () => loadAdminUsers(i);
      pg.appendChild(b);
    }
  } catch(e) { wrap.innerHTML = errState(e.message); }
}

async function adminUpdateUser(id, payload) {
  const res  = await apiFetch(`/admin/users/${id}`, { method:'PUT', body:JSON.stringify(payload) });
  const data = await res.json();
  if (!res.ok) { toast(data.error||'Failed','error'); return false; }
  toast('User updated ✓');
  loadAdminUsers();
  return true;
}

function promoteUser(id)              { if(confirm('Make this user an admin?'))     adminUpdateUser(id,{role:'admin'}); }
function demoteUser(id)               { if(confirm('Demote this admin to user?'))   adminUpdateUser(id,{role:'user'}); }
function toggleUserActive(id, active) { if(confirm(active?'Enable this account?':'Disable this account?')) adminUpdateUser(id,{is_active:active}); }
function verifyUser(id)               { adminUpdateUser(id,{is_verified:true}); }

// ── TEMPLATE HELPERS ─────────────────────────────────────────────
function ncCard(name, unit, actual, goal, color) {
  const pct  = goal > 0 ? Math.min((actual/goal)*100,100) : 0;
  const over = actual > goal;
  return `<div class="nutrient-item">
    <div class="nutrient-name">${name}</div>
    <div class="nutrient-value" style="color:${color}">${Math.round(actual)}</div>
    <div class="nutrient-unit">${unit} / ${Math.round(goal)}</div>
    <div class="progress-track"><div class="progress-fill" style="width:${pct}%;background:${over?'var(--rose)':color}"></div></div>
  </div>`;
}

function predHTML(p) {
  const pw  = p.predicted_weight;
  const d7  = (pw.after_7_days_kg  - (currentUser?.weight_kg||0)).toFixed(1);
  const d30 = (pw.after_30_days_kg - (currentUser?.weight_kg||0)).toFixed(1);
  return `<div class="card" style="margin-top:16px">
    <div class="card-title">⚖️ Weight Prediction</div>
    <div class="prediction-row">
      <div class="pred-card"><div class="pred-label">Current</div><div class="pred-weight pred-neutral">${currentUser?.weight_kg||'—'} kg</div></div>
      <div class="pred-card">
        <div class="pred-label">After 7 Days</div>
        <div class="pred-weight ${d7<0?'pred-down':'pred-up'}">${pw.after_7_days_kg} kg</div>
        <div class="pred-delta ${d7<0?'pred-down':'pred-up'}">${d7>0?'+':''}${d7} kg</div>
      </div>
      <div class="pred-card">
        <div class="pred-label">After 30 Days</div>
        <div class="pred-weight ${d30<0?'pred-down':'pred-up'}">${pw.after_30_days_kg} kg</div>
        <div class="pred-delta ${d30<0?'pred-down':'pred-up'}">${d30>0?'+':''}${d30} kg</div>
      </div>
    </div>
    <div style="margin-top:12px;font-size:12px;color:var(--muted);display:flex;gap:16px;flex-wrap:wrap">
      <span>TDEE: <strong style="color:var(--text)">${p.tdee} kcal</strong></span>
      <span>Consumed: <strong style="color:var(--teal)">${p.avg_daily_calories_consumed} kcal</strong></span>
      <span>Delta: <strong style="color:${p.daily_calorie_delta<0?'var(--teal)':'var(--rose)'}">${p.daily_calorie_delta>0?'+':''}${p.daily_calorie_delta} kcal/day</strong></span>
      ${p.days_to_target?`<span>Est. to target: <strong style="color:var(--amber)">${p.days_to_target} days</strong></span>`:''}
    </div>
  </div>`;
}

function errState(msg) { return `<div class="empty-state"><div class="empty-icon">⚠️</div><div>${msg}</div></div>`; }

// ── MICRO UTILS ──────────────────────────────────────────────────
function v(id)            { return document.getElementById(id)?.value || ''; }
function setText(id, txt) { const el=document.getElementById(id); if(el) el.textContent=txt; }
function setStat(id, val) { setText(id, val); }

function setDelta(id, delta) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = (delta > 0 ? '+' : '') + delta + ' kg';
  el.className   = `pred-delta ${delta < 0 ? 'pred-down' : 'pred-up'}`;
}

function showChart(imgId, emptyId, src) {
  const img = document.getElementById(imgId);
  const emp = document.getElementById(emptyId);
  if (img) { img.src = src; img.style.display = 'block'; }
  if (emp) emp.style.display = 'none';
}

function setBtnLoading(id, label) {
  const btn = document.getElementById(id);
  if (!btn) return null;
  const orig = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<div class="spinner"></div> ${label}`;
  return { btn, orig };
}

function resetBtn(handle, label) {
  if (!handle) return;
  handle.btn.disabled  = false;
  handle.btn.innerHTML = label;
}
