"""
Single-page web application for managing chores.

Served at GET /chores. All HTML, CSS, and JS are inlined — no external
dependencies, no build step.
"""


def generate_chores_ui_html() -> str:
    """Return the full HTML string for the /chores SPA."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chores</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #222; }
  a { color: inherit; text-decoration: none; }

  /* ---------- layout ---------- */
  header {
    background: #2c5282; color: #fff;
    padding: 0.75rem 1.5rem;
    display: flex; align-items: center; gap: 1rem;
  }
  header h1 { font-size: 1.25rem; font-weight: 700; }
  nav { display: flex; gap: 0; margin-left: auto; }
  nav button {
    background: transparent; border: none; color: #cbd5e0;
    padding: 0.5rem 1rem; cursor: pointer; font-size: 0.95rem;
    border-bottom: 3px solid transparent; transition: color 0.15s;
  }
  nav button:hover { color: #fff; }
  nav button.active { color: #fff; border-bottom-color: #63b3ed; }

  main { max-width: 900px; margin: 1.5rem auto; padding: 0 1rem; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }

  /* ---------- cards & tables ---------- */
  .card {
    background: #fff; border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    overflow: hidden; margin-bottom: 1.5rem;
  }
  .card-header {
    padding: 0.75rem 1rem; background: #ebf4ff;
    font-weight: 600; display: flex; align-items: center;
    justify-content: space-between;
  }
  table { width: 100%; border-collapse: collapse; }
  th {
    background: #f7fafc; padding: 0.6rem 1rem;
    text-align: left; font-size: 0.8rem; text-transform: uppercase;
    letter-spacing: 0.05em; color: #718096;
    border-bottom: 1px solid #e2e8f0;
  }
  td { padding: 0.65rem 1rem; border-bottom: 1px solid #f0f0f0; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tbody tr:hover { background: #f7fafc; cursor: pointer; }
  tbody tr.expanded { background: #ebf8ff; }

  /* detail / expansion rows */
  .detail-row td {
    background: #f0f9ff; padding: 1rem 1.25rem;
    cursor: default;
  }
  .detail-row:hover td { background: #f0f9ff; }
  .detail-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 0.4rem 2rem; margin-bottom: 0.75rem;
  }
  .detail-grid dt { font-size: 0.78rem; color: #718096; text-transform: uppercase; }
  .detail-grid dd { font-weight: 500; }

  /* ---------- status badges ---------- */
  .badge {
    display: inline-block; padding: 0.15em 0.55em;
    border-radius: 9999px; font-size: 0.75rem; font-weight: 600;
  }
  .badge-green { background: #c6f6d5; color: #276749; }
  .badge-yellow { background: #fefcbf; color: #744210; }
  .badge-red { background: #fed7d7; color: #9b2c2c; }
  .badge-grey { background: #e2e8f0; color: #4a5568; }
  .badge-purple { background: #e9d8fd; color: #553c9a; }

  /* ---------- buttons ---------- */
  .btn {
    display: inline-block; padding: 0.4rem 0.85rem;
    border: none; border-radius: 4px; cursor: pointer;
    font-size: 0.875rem; font-weight: 500; transition: opacity 0.15s;
  }
  .btn:disabled { opacity: 0.45; cursor: not-allowed; }
  .btn-primary { background: #3182ce; color: #fff; }
  .btn-primary:hover:not(:disabled) { background: #2b6cb0; }
  .btn-success { background: #38a169; color: #fff; }
  .btn-success:hover:not(:disabled) { background: #276749; }
  .btn-danger { background: #e53e3e; color: #fff; }
  .btn-danger:hover:not(:disabled) { background: #c53030; }
  .btn-ghost {
    background: transparent; color: #3182ce;
    border: 1px solid #bee3f8;
  }
  .btn-ghost:hover { background: #ebf8ff; }
  .btn-sm { padding: 0.25rem 0.6rem; font-size: 0.8rem; }

  /* ---------- forms ---------- */
  .form-row { display: flex; gap: 0.6rem; align-items: flex-end; flex-wrap: wrap; }
  .form-group { display: flex; flex-direction: column; gap: 0.25rem; }
  label { font-size: 0.8rem; color: #555; font-weight: 500; }
  input[type="text"], input[type="number"], input[type="date"], select {
    padding: 0.4rem 0.6rem; border: 1px solid #cbd5e0;
    border-radius: 4px; font-size: 0.9rem; width: 100%;
    background: #fff;
  }
  input[type="number"] { width: 5rem; }
  .inline-form { padding: 0.75rem 1rem; background: #f7fafc; border-top: 1px solid #e2e8f0; }
  .inline-form .form-row { margin-bottom: 0.5rem; }

  /* ---------- error banner ---------- */
  .error-banner {
    background: #fff5f5; border: 1px solid #feb2b2;
    color: #c53030; border-radius: 4px;
    padding: 0.5rem 0.85rem; margin: 0.5rem 0;
    font-size: 0.875rem; display: none;
  }
  .error-banner.visible { display: block; }

  /* ---------- section toggle ---------- */
  .section-toggle { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
  .section-toggle button {
    padding: 0.4rem 1rem; border: 1px solid #cbd5e0;
    background: #fff; border-radius: 4px; cursor: pointer;
    font-size: 0.875rem;
  }
  .section-toggle button.active { background: #2c5282; color: #fff; border-color: #2c5282; }

  /* ---------- rankings ---------- */
  .rankings-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 0.5rem; margin-top: 0.5rem;
  }
  .ranking-item { display: flex; align-items: center; gap: 0.5rem; }
  .ranking-item label { flex: 1; font-size: 0.85rem; }
  .ranking-item input { width: 4rem; }

  /* ---------- audit ---------- */
  pre.json-preview {
    background: #1a202c; color: #e2e8f0; padding: 0.75rem 1rem;
    border-radius: 4px; font-size: 0.78rem; overflow-x: auto;
    white-space: pre-wrap; word-break: break-word;
  }
  .op-INSERT { color: #276749; font-weight: 600; }
  .op-UPDATE { color: #744210; font-weight: 600; }
  .op-DELETE { color: #9b2c2c; font-weight: 600; }

  /* ---------- empty state ---------- */
  .empty { padding: 2rem; text-align: center; color: #a0aec0; font-style: italic; }
</style>
</head>
<body>

<header>
  <h1>🧹 Chores</h1>
  <nav>
    <button id="tab-btn-chores"    class="active" onclick="switchTab('chores')">Chores</button>
    <button id="tab-btn-management"               onclick="switchTab('management')">Management</button>
    <button id="tab-btn-audit"                    onclick="switchTab('audit')">Audit Log</button>
  </nav>
</header>

<main>
  <!-- ============================================================ TAB 1: CHORES -->
  <div id="tab-chores" class="tab-panel active">
    <div class="card">
      <div class="card-header">
        Chores
        <button class="btn btn-ghost btn-sm" onclick="loadChores()">↻ Refresh</button>
      </div>
      <div id="chores-error" class="error-banner"></div>
      <table>
        <thead>
          <tr>
            <th>Chore</th>
            <th>Due Date</th>
            <th>Next Executor</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="chores-tbody">
          <tr><td colspan="4" class="empty">Loading…</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ============================================================ TAB 2: MANAGEMENT -->
  <div id="tab-management" class="tab-panel">
    <div class="section-toggle">
      <button id="mgmt-btn-people" class="active" onclick="switchMgmtSection('people')">People</button>
      <button id="mgmt-btn-chores"                onclick="switchMgmtSection('chores')">Chores</button>
    </div>

    <!-- People section -->
    <div id="mgmt-people">
      <div class="card">
        <div class="card-header">
          People
          <button class="btn btn-primary btn-sm" onclick="showAddPersonForm()">+ Add Person</button>
        </div>
        <div id="people-error" class="error-banner"></div>
        <table>
          <thead>
            <tr><th>Name</th><th>Ordinal</th><th>Avatar</th><th></th></tr>
          </thead>
          <tbody id="people-tbody">
            <tr><td colspan="4" class="empty">Loading…</td></tr>
          </tbody>
        </table>
        <div id="add-person-form" class="inline-form" style="display:none">
          <div class="form-row">
            <div class="form-group">
              <label>Name</label>
              <input type="text" id="new-person-name" placeholder="Name">
            </div>
            <div class="form-group">
              <label>Ordinal</label>
              <input type="number" id="new-person-ordinal" min="1" placeholder="1">
            </div>
            <div class="form-group">
              <label>Avatar</label>
              <input type="text" id="new-person-avatar" placeholder="avatar.png">
            </div>
            <div class="form-group" style="justify-content:flex-end">
              <button class="btn btn-success" onclick="addPerson()">Save</button>
              <button class="btn btn-ghost" onclick="hideAddPersonForm()" style="margin-top:0.25rem">Cancel</button>
            </div>
          </div>
          <div id="add-person-error" class="error-banner"></div>
        </div>
      </div>
    </div>

    <!-- Chores management section -->
    <div id="mgmt-chores" style="display:none">
      <div class="card">
        <div class="card-header">
          Chores
          <button class="btn btn-primary btn-sm" onclick="showAddChoreForm()">+ Add Chore</button>
        </div>
        <div id="mgmt-chores-error" class="error-banner"></div>
        <table>
          <thead>
            <tr><th>Name</th><th>Frequency (weeks)</th><th></th></tr>
          </thead>
          <tbody id="mgmt-chores-tbody">
            <tr><td colspan="3" class="empty">Loading…</td></tr>
          </tbody>
        </table>
        <div id="add-chore-form" class="inline-form" style="display:none">
          <div class="form-row">
            <div class="form-group" style="flex:1">
              <label>Name</label>
              <input type="text" id="new-chore-name" placeholder="Chore name">
            </div>
            <div class="form-group">
              <label>Frequency (weeks)</label>
              <input type="number" id="new-chore-freq" min="1" placeholder="1">
            </div>
            <div class="form-group" style="justify-content:center;align-self:flex-end;padding-bottom:0.35rem">
              <label style="display:flex;align-items:center;gap:0.4rem;cursor:pointer">
                <input type="checkbox" id="new-chore-same-person"> Same person next time
              </label>
            </div>
            <div class="form-group" style="justify-content:flex-end">
              <button class="btn btn-success" onclick="addChore()">Save</button>
              <button class="btn btn-ghost" onclick="hideAddChoreForm()" style="margin-top:0.25rem">Cancel</button>
            </div>
          </div>
          <div id="add-chore-error" class="error-banner"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- ============================================================ TAB 3: AUDIT LOG -->
  <div id="tab-audit" class="tab-panel">
    <div class="card">
      <div class="card-header">
        Audit Log <span style="font-weight:400;font-size:0.85rem;color:#718096;">(last 100 changes)</span>
        <button class="btn btn-ghost btn-sm" onclick="loadAudit()">↻ Refresh</button>
      </div>
      <div id="audit-error" class="error-banner"></div>
      <table>
        <thead>
          <tr>
            <th>When</th>
            <th>Table</th>
            <th>Operation</th>
            <th>Record ID</th>
            <th>Changed By</th>
          </tr>
        </thead>
        <tbody id="audit-tbody">
          <tr><td colspan="5" class="empty">Loading…</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</main>

<script>
// ============================================================
// State
// ============================================================
let people = [];      // [{id, name, ordinal, avatar, ...}]
let allChores = [];   // from /chores list endpoint
let summary = [];     // from /summary endpoint (chores + state + rankings)
let peopleMap = {};   // id -> {name, ordinal}
let choreStates = {}; // chore_id -> ChoreStateResponse

const API = '/api/v1/chores';

// ============================================================
// Utilities
// ============================================================
async function api(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  const json = await res.json().catch(() => null);
  if (!res.ok) {
    const msg = json?.detail || json?.error || res.statusText;
    throw new Error(msg);
  }
  return json;
}

function showError(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
}
function clearError(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = '';
  el.classList.remove('visible');
}

function fmtDate(s) {
  if (!s) return '—';
  // s is YYYY-MM-DD
  return s;
}
function fmtTs(s) {
  if (!s) return '—';
  return s.replace('T', ' ').substring(0, 16);
}

function dueBadge(dateStr) {
  if (!dateStr) return '<span class="badge badge-grey">No date</span>';
  const due = new Date(dateStr);
  const today = new Date();
  today.setHours(0,0,0,0);
  const diff = Math.floor((due - today) / 86400000); // days
  if (diff < 0)  return `<span class="badge badge-red">Overdue ${-diff}d</span>`;
  if (diff === 0) return `<span class="badge badge-yellow">Due today</span>`;
  if (diff <= 7)  return `<span class="badge badge-yellow">In ${diff}d</span>`;
  return `<span class="badge badge-green">In ${diff}d</span>`;
}

// ============================================================
// Tab navigation
// ============================================================
const TABS = ['chores', 'management', 'audit'];

function switchTab(name) {
  TABS.forEach(t => {
    document.getElementById('tab-' + t).classList.toggle('active', t === name);
    document.getElementById('tab-btn-' + t).classList.toggle('active', t === name);
  });
  // Lazy-load data for each tab
  if (name === 'chores')     loadChores();
  if (name === 'management') loadManagement();
  if (name === 'audit')      loadAudit();
  location.hash = name;
}

function switchMgmtSection(section) {
  ['people', 'chores'].forEach(s => {
    document.getElementById('mgmt-' + s).style.display = s === section ? '' : 'none';
    document.getElementById('mgmt-btn-' + s).classList.toggle('active', s === section);
  });
}

// ============================================================
// TAB 1 — Chores List
// ============================================================
async function loadChores() {
  clearError('chores-error');
  const tbody = document.getElementById('chores-tbody');
  tbody.innerHTML = '<tr><td colspan="4" class="empty">Loading…</td></tr>';
  try {
    const [summaryRes, peopleRes] = await Promise.all([
      api('GET', '/summary'),
      api('GET', '/people'),
    ]);
    people = peopleRes.data || [];
    summary = summaryRes.data?.chores || [];
    peopleMap = Object.fromEntries(people.map(p => [p.id, p]));

    // Sort: primary by next_execution_date asc (null last), secondary by next executor ordinal asc
    summary.sort((a, b) => {
      const da = a.state?.next_execution_date;
      const db = b.state?.next_execution_date;
      if (da && db) {
        if (da !== db) return da < db ? -1 : 1; // ascending
      } else if (da) return -1;
      else if (db) return 1;
      // secondary: ordinal asc
      const oa = peopleMap[a.state?.next_executor_id]?.ordinal ?? Infinity;
      const ob = peopleMap[b.state?.next_executor_id]?.ordinal ?? Infinity;
      return oa - ob;
    });

    if (summary.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty">No chores yet. Add some in Management.</td></tr>';
      return;
    }

    tbody.innerHTML = summary.map((chore, i) => {
      const state = chore.state || {};
      const nextPerson = peopleMap[state.next_executor_id];
      const nextName = nextPerson ? nextPerson.name : '—';
      const samePersonBadge = chore.same_person_next_time
        ? ' <span class="badge badge-purple" title="Same person next time">📌 Always same</span>'
        : '';
      return `
        <tr id="chore-row-${i}" onclick="toggleChoreDetail(${i})" data-idx="${i}">
          <td><strong>${esc(chore.name)}</strong>${samePersonBadge}</td>
          <td>${fmtDate(state.next_execution_date)} ${dueBadge(state.next_execution_date)}</td>
          <td>${esc(nextName)}</td>
          <td>${state.next_executor_id ? '' : '<span class="badge badge-grey">Unscheduled</span>'}</td>
        </tr>
        <tr id="chore-detail-${i}" class="detail-row" style="display:none">
          <td colspan="4">${choreDetailHTML(chore, state)}</td>
        </tr>`;
    }).join('');
  } catch(e) {
    showError('chores-error', e.message);
    tbody.innerHTML = '';
  }
}

function choreDetailHTML(chore, state) {
  const lastPerson = peopleMap[state.last_executor_id];
  const nextPerson = peopleMap[state.next_executor_id];
  const canMarkDone = !!state.next_executor_id;
  return `
    <dl class="detail-grid">
      <dt>Last Executor</dt><dd>${lastPerson ? esc(lastPerson.name) : '—'}</dd>
      <dt>Last Date</dt><dd>${fmtDate(state.last_execution_date)}</dd>
      <dt>Next Executor</dt><dd>${nextPerson ? esc(nextPerson.name) : '—'}</dd>
      <dt>Next Date</dt><dd>${fmtDate(state.next_execution_date)}</dd>
      <dt>Frequency</dt><dd>Every ${chore.frequency_in_weeks} week${chore.frequency_in_weeks !== 1 ? 's' : ''}</dd>
    </dl>
    <div id="done-error-${chore.id}" class="error-banner"></div>
    <button class="btn btn-success btn-sm"
      ${canMarkDone ? '' : 'disabled title="No next executor scheduled"'}
      onclick="markDone(${chore.id}, ${state.next_executor_id})">
      ✓ Mark as Done
    </button>`;
}

function toggleChoreDetail(i) {
  const detailRow = document.getElementById('chore-detail-' + i);
  const mainRow   = document.getElementById('chore-row-' + i);
  const isHidden = detailRow.style.display === 'none';
  detailRow.style.display = isHidden ? '' : 'none';
  mainRow.classList.toggle('expanded', isHidden);
}

async function markDone(choreId, executorId) {
  clearError('done-error-' + choreId);
  try {
    await api('POST', '/executions', { chore_id: choreId, executor_id: executorId });
    await loadChores();
  } catch(e) {
    showError('done-error-' + choreId, e.message);
  }
}

// ============================================================
// TAB 2 — Management
// ============================================================
async function loadManagement() {
  await Promise.all([loadPeople(), loadMgmtChores()]);
}

// --- People ---
async function loadPeople() {
  clearError('people-error');
  const tbody = document.getElementById('people-tbody');
  tbody.innerHTML = '<tr><td colspan="4" class="empty">Loading…</td></tr>';
  try {
    const res = await api('GET', '/people');
    people = (res.data || []).slice().sort((a, b) => a.ordinal - b.ordinal);
    const choresList = allChores.length ? allChores : (await api('GET', '/chores')).data || [];
    allChores = choresList;
    if (people.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty">No people yet.</td></tr>';
      return;
    }
    tbody.innerHTML = people.map(p => personRowHTML(p)).join('');
  } catch(e) {
    showError('people-error', e.message);
    tbody.innerHTML = '';
  }
}

function personRowHTML(p) {
  return `
    <tr id="person-row-${p.id}">
      <td>
        <span class="btn-ghost" style="cursor:pointer;color:#2b6cb0;font-weight:500"
          onclick="toggleRankings(${p.id})">${esc(p.name)}</span>
      </td>
      <td>${p.ordinal}</td>
      <td>${esc(p.avatar)}</td>
      <td style="display:flex;gap:0.4rem;flex-wrap:wrap">
        <button class="btn btn-ghost btn-sm" onclick="showEditPerson(${p.id})">Edit</button>
        <button class="btn btn-ghost btn-sm" onclick="toggleRankings(${p.id})">Ratings</button>
        <button class="btn btn-danger btn-sm" onclick="deletePerson(${p.id}, '${esc(p.name)}')">Delete</button>
      </td>
    </tr>
    <tr id="person-edit-${p.id}" style="display:none">
      <td colspan="4" class="inline-form">
        <div class="form-row">
          <div class="form-group" style="flex:1">
            <label>Name</label>
            <input type="text" id="edit-name-${p.id}" value="${esc(p.name)}">
          </div>
          <div class="form-group">
            <label>Ordinal</label>
            <input type="number" id="edit-ordinal-${p.id}" min="1" value="${p.ordinal}">
          </div>
          <div class="form-group" style="flex:1">
            <label>Avatar</label>
            <input type="text" id="edit-avatar-${p.id}" value="${esc(p.avatar)}">
          </div>
          <div class="form-group" style="justify-content:flex-end">
            <button class="btn btn-success btn-sm" onclick="savePerson(${p.id})">Save</button>
            <button class="btn btn-ghost btn-sm" onclick="hideEditPerson(${p.id})" style="margin-top:0.25rem">Cancel</button>
          </div>
        </div>
        <div id="edit-person-error-${p.id}" class="error-banner"></div>
      </td>
    </tr>
    <tr id="person-rankings-${p.id}" style="display:none">
      <td colspan="4" class="inline-form">
        <div id="rankings-error-${p.id}" class="error-banner"></div>
        <div class="rankings-grid" id="rankings-grid-${p.id}">Loading rankings…</div>
        <button class="btn btn-success btn-sm" style="margin-top:0.75rem"
          onclick="saveRankings(${p.id})">Save Rankings</button>
      </td>
    </tr>`;
}

function showEditPerson(id) {
  document.getElementById('person-edit-' + id).style.display = '';
}
function hideEditPerson(id) {
  document.getElementById('person-edit-' + id).style.display = 'none';
  clearError('edit-person-error-' + id);
}

async function savePerson(id) {
  clearError('edit-person-error-' + id);
  const name   = document.getElementById('edit-name-' + id).value.trim();
  const ordinal = parseInt(document.getElementById('edit-ordinal-' + id).value);
  const avatar = document.getElementById('edit-avatar-' + id).value.trim();
  if (!name || !avatar || isNaN(ordinal)) {
    showError('edit-person-error-' + id, 'All fields are required.');
    return;
  }
  try {
    await api('PUT', '/people/' + id, { name, ordinal, avatar });
    await loadPeople();
  } catch(e) {
    showError('edit-person-error-' + id, e.message);
  }
}

async function deletePerson(id, name) {
  if (!confirm(`Delete person "${name}"? This will also remove their executions and rankings.`)) return;
  clearError('people-error');
  try {
    await api('DELETE', '/people/' + id);
    await loadPeople();
  } catch(e) {
    showError('people-error', e.message);
  }
}

async function toggleRankings(personId) {
  const row = document.getElementById('person-rankings-' + personId);
  const isHidden = row.style.display === 'none';
  row.style.display = isHidden ? '' : 'none';
  if (isHidden) await loadRankingsForPerson(personId);
}

async function loadRankingsForPerson(personId) {
  clearError('rankings-error-' + personId);
  const grid = document.getElementById('rankings-grid-' + personId);
  try {
    const [rankRes, choreRes] = await Promise.all([
      api('GET', '/rankings?person_id=' + personId),
      allChores.length ? Promise.resolve({ data: allChores }) : api('GET', '/chores'),
    ]);
    allChores = choreRes.data || [];
    const ratings = Object.fromEntries((rankRes.data || []).map(r => [r.chore_id, r.rating]));
    const rankableChores = allChores.filter(c => !c.same_person_next_time);
    if (rankableChores.length === 0) {
      grid.innerHTML = '<em>No chores to rank.</em>';
      return;
    }
    grid.innerHTML = rankableChores.map(c => `
      <div class="ranking-item">
        <label for="rank-${personId}-${c.id}">${esc(c.name)}</label>
        <input type="number" id="rank-${personId}-${c.id}"
          min="1" max="10" placeholder="—"
          value="${ratings[c.id] !== undefined ? ratings[c.id] : ''}">
      </div>`).join('');
  } catch(e) {
    showError('rankings-error-' + personId, e.message);
    grid.innerHTML = '';
  }
}

async function saveRankings(personId) {
  clearError('rankings-error-' + personId);
  const errors = [];
  for (const chore of allChores.filter(c => !c.same_person_next_time)) {
    const input = document.getElementById(`rank-${personId}-${chore.id}`);
    if (!input) continue;
    const val = input.value.trim();
    if (val === '') continue;
    const rating = parseInt(val);
    if (isNaN(rating) || rating < 1 || rating > 10) {
      errors.push(`Rating for "${chore.name}" must be 1–10.`);
      continue;
    }
    try {
      await api('POST', '/rankings', { person_id: personId, chore_id: chore.id, rating });
    } catch(e) {
      errors.push(`"${chore.name}": ${e.message}`);
    }
  }
  if (errors.length) showError('rankings-error-' + personId, errors.join(' | '));
}

function showAddPersonForm() {
  document.getElementById('add-person-form').style.display = '';
  clearError('add-person-error');
}
function hideAddPersonForm() {
  document.getElementById('add-person-form').style.display = 'none';
}

async function addPerson() {
  clearError('add-person-error');
  const name   = document.getElementById('new-person-name').value.trim();
  const ordinal = parseInt(document.getElementById('new-person-ordinal').value);
  const avatar = document.getElementById('new-person-avatar').value.trim();
  if (!name || !avatar || isNaN(ordinal)) {
    showError('add-person-error', 'All fields are required.');
    return;
  }
  try {
    await api('POST', '/people', { name, ordinal, avatar });
    document.getElementById('new-person-name').value = '';
    document.getElementById('new-person-ordinal').value = '';
    document.getElementById('new-person-avatar').value = '';
    hideAddPersonForm();
    await loadPeople();
  } catch(e) {
    showError('add-person-error', e.message);
  }
}

// --- Chores management ---
async function loadMgmtChores() {
  clearError('mgmt-chores-error');
  const tbody = document.getElementById('mgmt-chores-tbody');
  tbody.innerHTML = '<tr><td colspan="3" class="empty">Loading…</td></tr>';
  try {
    const [choreRes, summaryRes] = await Promise.all([
      api('GET', '/chores'),
      api('GET', '/summary'),
    ]);
    allChores = (choreRes.data || []).slice().sort((a, b) => a.name.localeCompare(b.name));
    const summaryChores = summaryRes.data?.chores || [];
    choreStates = Object.fromEntries(summaryChores.map(c => [c.id, c.state || {}]));
    if (allChores.length === 0) {
      tbody.innerHTML = '<tr><td colspan="3" class="empty">No chores yet.</td></tr>';
      return;
    }
    tbody.innerHTML = allChores.map(c => choreRowHTML(c)).join('');
  } catch(e) {
    showError('mgmt-chores-error', e.message);
    tbody.innerHTML = '';
  }
}

function choreRowHTML(c) {
  return `
    <tr id="chore-mgmt-row-${c.id}">
      <td>${esc(c.name)}${c.same_person_next_time ? ' <span class="badge badge-purple">📌 Same person</span>' : ''}</td>
      <td>${c.frequency_in_weeks}</td>
      <td style="display:flex;gap:0.4rem;flex-wrap:wrap">
        <button class="btn btn-ghost btn-sm" onclick="showEditChore(${c.id})">Edit</button>
        <button class="btn btn-ghost btn-sm" onclick="showEditSchedule(${c.id})">Schedule</button>
        <button class="btn btn-danger btn-sm" onclick="deleteChore(${c.id}, '${esc(c.name)}')">Delete</button>
      </td>
    </tr>
    <tr id="chore-mgmt-edit-${c.id}" style="display:none">
      <td colspan="3" class="inline-form">
        <div class="form-row">
          <div class="form-group" style="flex:1">
            <label>Name</label>
            <input type="text" id="edit-chore-name-${c.id}" value="${esc(c.name)}">
          </div>
          <div class="form-group">
            <label>Frequency (weeks)</label>
            <input type="number" id="edit-chore-freq-${c.id}" min="1" value="${c.frequency_in_weeks}">
          </div>
          <div class="form-group" style="justify-content:center;align-self:flex-end;padding-bottom:0.35rem">
            <label style="display:flex;align-items:center;gap:0.4rem;cursor:pointer">
              <input type="checkbox" id="edit-chore-same-person-${c.id}" ${c.same_person_next_time ? 'checked' : ''}> Same person next time
            </label>
          </div>
          <div class="form-group" style="justify-content:flex-end">
            <button class="btn btn-success btn-sm" onclick="saveChore(${c.id})">Save</button>
            <button class="btn btn-ghost btn-sm" onclick="hideEditChore(${c.id})" style="margin-top:0.25rem">Cancel</button>
          </div>
        </div>
        <div id="edit-chore-error-${c.id}" class="error-banner"></div>
      </td>
    </tr>
    <tr id="chore-sched-edit-${c.id}" style="display:none">
      <td colspan="3" class="inline-form">
        <strong style="font-size:0.85rem;display:block;margin-bottom:0.5rem">Edit Next Execution</strong>
        <div class="form-row">
          <div class="form-group">
            <label>Next Due Date</label>
            <input type="date" id="sched-date-${c.id}">
          </div>
          <div class="form-group" style="flex:1">
            <label>Next Executor</label>
            <select id="sched-executor-${c.id}"></select>
          </div>
          <div class="form-group" style="justify-content:flex-end">
            <button class="btn btn-success btn-sm" onclick="saveSchedule(${c.id})">Save</button>
            <button class="btn btn-ghost btn-sm" onclick="hideEditSchedule(${c.id})" style="margin-top:0.25rem">Cancel</button>
          </div>
        </div>
        <div id="sched-error-${c.id}" class="error-banner"></div>
      </td>
    </tr>`;
}

function showEditChore(id) {
  hideEditSchedule(id);
  document.getElementById('chore-mgmt-edit-' + id).style.display = '';
}
function hideEditChore(id) {
  document.getElementById('chore-mgmt-edit-' + id).style.display = 'none';
  clearError('edit-chore-error-' + id);
}

function showEditSchedule(choreId) {
  hideEditChore(choreId);
  const state = choreStates[choreId] || {};
  // Pre-populate date
  document.getElementById('sched-date-' + choreId).value = state.next_execution_date || '';
  // Populate people dropdown
  const sel = document.getElementById('sched-executor-' + choreId);
  sel.innerHTML = '<option value="">\u2014 None \u2014</option>' +
    people.map(p =>
      `<option value="${p.id}" ${p.id === state.next_executor_id ? 'selected' : ''}>${esc(p.name)}</option>`
    ).join('');
  clearError('sched-error-' + choreId);
  document.getElementById('chore-sched-edit-' + choreId).style.display = '';
}
function hideEditSchedule(id) {
  const el = document.getElementById('chore-sched-edit-' + id);
  if (el) el.style.display = 'none';
  clearError('sched-error-' + id);
}

async function saveSchedule(choreId) {
  clearError('sched-error-' + choreId);
  const date = document.getElementById('sched-date-' + choreId).value;
  const executorVal = document.getElementById('sched-executor-' + choreId).value;
  const next_executor_id = executorVal ? parseInt(executorVal) : null;
  if (!date && !next_executor_id) {
    showError('sched-error-' + choreId, 'Please provide a date or select an executor.');
    return;
  }
  try {
    await api('PUT', '/executions/next-executor', {
      chore_id: choreId,
      next_executor_id: next_executor_id,
      next_execution_date: date || null,
    });
    hideEditSchedule(choreId);
    await loadMgmtChores();
  } catch(e) {
    showError('sched-error-' + choreId, e.message);
  }
}

async function saveChore(id) {
  clearError('edit-chore-error-' + id);
  const name = document.getElementById('edit-chore-name-' + id).value.trim();
  const freq = parseInt(document.getElementById('edit-chore-freq-' + id).value);
  const samePersonNextTime = document.getElementById('edit-chore-same-person-' + id).checked;
  if (!name || isNaN(freq) || freq < 1) {
    showError('edit-chore-error-' + id, 'Name is required and frequency must be ≥ 1.');
    return;
  }
  try {
    await api('PUT', '/chores/' + id, { name, frequency_in_weeks: freq, same_person_next_time: samePersonNextTime });
    await loadMgmtChores();
  } catch(e) {
    showError('edit-chore-error-' + id, e.message);
  }
}

async function deleteChore(id, name) {
  if (!confirm(`Delete chore "${name}"? This will also remove its state, executions, and rankings.`)) return;
  clearError('mgmt-chores-error');
  try {
    await api('DELETE', '/chores/' + id);
    await loadMgmtChores();
  } catch(e) {
    showError('mgmt-chores-error', e.message);
  }
}

function showAddChoreForm() {
  document.getElementById('add-chore-form').style.display = '';
  clearError('add-chore-error');
}
function hideAddChoreForm() {
  document.getElementById('add-chore-form').style.display = 'none';
}

async function addChore() {
  clearError('add-chore-error');
  const name = document.getElementById('new-chore-name').value.trim();
  const freq = parseInt(document.getElementById('new-chore-freq').value);
  const samePersonNextTime = document.getElementById('new-chore-same-person').checked;
  if (!name || isNaN(freq) || freq < 1) {
    showError('add-chore-error', 'Name is required and frequency must be ≥ 1.');
    return;
  }
  try {
    await api('POST', '/chores', { name, frequency_in_weeks: freq, same_person_next_time: samePersonNextTime });
    document.getElementById('new-chore-name').value = '';
    document.getElementById('new-chore-freq').value = '';
    document.getElementById('new-chore-same-person').checked = false;
    hideAddChoreForm();
    await loadMgmtChores();
  } catch(e) {
    showError('add-chore-error', e.message);
  }
}

// ============================================================
// TAB 3 — Audit Log
// ============================================================
async function loadAudit() {
  clearError('audit-error');
  const tbody = document.getElementById('audit-tbody');
  tbody.innerHTML = '<tr><td colspan="5" class="empty">Loading…</td></tr>';
  try {
    const res = await api('GET', '/audit');
    const entries = (res.data || []).slice(0, 100);
    if (entries.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty">No audit entries yet.</td></tr>';
      return;
    }
    tbody.innerHTML = entries.map((e, i) => auditRowHTML(e, i)).join('');
  } catch(err) {
    showError('audit-error', err.message);
    tbody.innerHTML = '';
  }
}

function auditRowHTML(e, i) {
  const opClass = 'op-' + e.operation;
  const hasDiff = e.before_values || e.after_values;
  return `
    <tr ${hasDiff ? `onclick="toggleAuditDetail(${i})" style="cursor:pointer"` : ''}>
      <td>${fmtTs(e.changed_at)}</td>
      <td>${esc(e.table_name)}</td>
      <td><span class="${opClass}">${esc(e.operation)}</span></td>
      <td>${e.record_id}</td>
      <td>${esc(e.changed_by || '—')}</td>
    </tr>
    ${hasDiff ? `
    <tr id="audit-detail-${i}" class="detail-row" style="display:none">
      <td colspan="5">
        ${e.before_values ? `<p style="margin-bottom:0.3rem;font-size:0.8rem;color:#718096">Before</p><pre class="json-preview">${fmtJson(e.before_values)}</pre>` : ''}
        ${e.after_values  ? `<p style="margin:0.5rem 0 0.3rem;font-size:0.8rem;color:#718096">After</p><pre class="json-preview">${fmtJson(e.after_values)}</pre>` : ''}
      </td>
    </tr>` : ''}`;
}

function toggleAuditDetail(i) {
  const row = document.getElementById('audit-detail-' + i);
  if (row) row.style.display = row.style.display === 'none' ? '' : 'none';
}

function fmtJson(s) {
  try { return esc(JSON.stringify(JSON.parse(s), null, 2)); }
  catch { return esc(s); }
}

// ============================================================
// Escape helper (XSS prevention)
// ============================================================
function esc(s) {
  if (s === null || s === undefined) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ============================================================
// Bootstrap
// ============================================================
(function init() {
  const hash = location.hash.replace('#', '') || 'chores';
  const validTab = ['chores', 'management', 'audit'].includes(hash) ? hash : 'chores';
  switchTab(validTab);

  window.addEventListener('hashchange', () => {
    const h = location.hash.replace('#', '');
    if (['chores', 'management', 'audit'].includes(h)) {
      switchTab(h);
    }
  });
})();
</script>
</body>
</html>"""
